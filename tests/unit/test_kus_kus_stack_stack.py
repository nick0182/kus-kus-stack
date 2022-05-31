import aws_cdk as core
import aws_cdk.assertions as assertions

from kus_kus_stack.kus_kus_stack_stack import KusKusStackStack

# example tests. To run these tests, uncomment this file along with the example
# resource in kus_kus_stack/kus_kus_stack_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = KusKusStackStack(app, "kus-kus-stack")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
