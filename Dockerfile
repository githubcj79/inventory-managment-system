FROM public.ecr.aws/lambda/python:3.9

# Copy function code and requirements
COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY common/ ${LAMBDA_TASK_ROOT}/common/

# Install the specified requirements
RUN pip install -r requirements.txt

# Set the CMD to your handler
CMD [ "common.app.lambda_handler" ]
