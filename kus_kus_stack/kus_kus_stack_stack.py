import aws_cdk
from aws_cdk import (
    Stack,
    aws_eks as eks,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_opensearchservice as open_search,
    aws_elasticache as elasticache
)
from constructs import Construct
import os


class KusKusStackStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, synthesizer: aws_cdk.IStackSynthesizer, **kwargs) -> None:
        super().__init__(scope, construct_id, synthesizer=synthesizer, **kwargs)
        vpc = self.create_vpc()
        cluster = self.create_cluster(vpc)
        self.add_managed_nodegroup(cluster)
        self.create_namespace(cluster)
        self.configure_service_account(cluster)
        self.create_opensearch_cluster(cluster)
        self.create_elasticache_cluster(cluster)

    def create_vpc(self) -> ec2.Vpc:
        nat_gateway_provider = ec2.NatProvider.instance(instance_type=ec2.InstanceType('t3.small'))
        return ec2.Vpc(self, id='kus-kus-vpc', nat_gateway_provider=nat_gateway_provider)

    # FIXME: create vpc with nat instances instead of default nat gateways
    def create_cluster(self, vpc: ec2.Vpc) -> eks.Cluster:
        return eks.Cluster(self, id='kus-kus-cluster', version=eks.KubernetesVersion.V1_21, default_capacity=0,
                           endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE, vpc=vpc)

    def add_managed_nodegroup(self, cluster: eks.Cluster):
        cluster.add_nodegroup_capacity(id='ng-spot', instance_types=[ec2.InstanceType('t3.small')], min_size=2,
                                       capacity_type=eks.CapacityType.SPOT)

    def create_namespace(self, cluster: eks.Cluster):
        cluster.add_manifest('bot', {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': 'bot'
            }
        })

    def configure_service_account(self, cluster: eks.Cluster):
        read_s3_service_account = cluster.add_service_account(id='kus-kus-images', namespace='bot')
        main_images_bucket = s3.Bucket.from_bucket_arn(self, id='main-images-bucket',
                                                       bucket_arn='arn:aws:s3:::kuskus-main-images')
        step_images_bucket = s3.Bucket.from_bucket_arn(self, id='step-images-bucket',
                                                       bucket_arn='arn:aws:s3:::kuskus-step-images')
        main_images_bucket.grant_read(read_s3_service_account)
        step_images_bucket.grant_read(read_s3_service_account)

    # FIXME: username and password don't get passed to deployment
    def create_opensearch_cluster(self, cluster: eks.Cluster):
        open_search_master_username = os.getenv('OPEN_SEARCH_MASTER_USERNAME')
        open_search_master_password = os.getenv('OPEN_SEARCH_MASTER_PASSWORD')
        open_search.Domain(self, id='kus-kus-search', domain_name='kus-kus-search',
                           version=open_search.EngineVersion.OPENSEARCH_1_2,
                           capacity=open_search.CapacityConfig(
                               data_node_instance_type='t3.small.search', data_nodes=1),
                           enable_version_upgrade=True, enforce_https=True,
                           encryption_at_rest=open_search.EncryptionAtRestOptions(enabled=True),
                           fine_grained_access_control=open_search.AdvancedSecurityOptions(
                               master_user_name=open_search_master_username,
                               master_user_password=aws_cdk.SecretValue.unsafe_plain_text(
                                   secret=open_search_master_password)),
                           node_to_node_encryption=True, removal_policy=aws_cdk.RemovalPolicy.DESTROY,
                           security_groups=[cluster.cluster_security_group], vpc=cluster.vpc,
                           vpc_subnets=[ec2.SubnetSelection(subnets=[cluster.vpc.private_subnets[1]])])

    def create_elasticache_cluster(self, cluster: eks.Cluster):
        private_subnet = cluster.vpc.private_subnets[0]
        elasticache.CfnSubnetGroup(self, "redis", description="my subnet group", subnet_ids=[private_subnet.subnet_id],
                                   cache_subnet_group_name="redisSubnetGroup")
        elasticache.CfnCacheCluster(self, id='kus-kus-cache', cache_node_type='cache.t3.small', engine='redis',
                                    num_cache_nodes=1, auto_minor_version_upgrade=True,
                                    cache_subnet_group_name="redisSubnetGroup",
                                    cluster_name='kus-kus-cache', engine_version='6.2', port=6379,
                                    preferred_availability_zone=private_subnet.availability_zone,
                                    vpc_security_group_ids=[cluster.cluster_security_group.security_group_id])
