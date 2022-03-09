# Deploy a Micro ETL Pipeline using AWS Lambda, EventBridge and S3

This `AWS CDK` project creates the infrastructure needed to implement a serverless micro ETL pipeline. An `EventBridge` rule schedules the provided `Lambda` function to run every Monday at 9am UTC to pull stock data for a number of symbols using the `Alpha Vantage API` (free version), transform it using the `pandas` library and save the resulting dataset as CSV in `S3`.

## Deployment

To deploy this project, make sure you have installed and configured the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) and [Docker](https://docs.docker.com/get-docker/) first. Then get your free API key from [Alpha Vantage](https://www.alphavantage.co/).

Add the API key to AWS Secrets Manager using the following CLI command. Note that you should store the key in the same region you intend to deploy the infrastructure.

```
$ aws secretsmanager create-secret \
    --name AlphaVantageApiKey \
    --secret-string <YOUR-API_KEY> \
    --region <YOUR-AWS-REGION>
```

Then clone the repo and manually create a virtualenv inside the project directory. For MacOs and Linux, run the following:

```
$ python3 -m venv .venv
```

Activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are using Windows, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

If this is the first CDK project you are deploying to your default region then bootstrap CDK:

```
$ cdk bootstrap
```

At this point you can synthesize the CloudFormation template for this code

```
$ cdk synth
```

Everything is now ready, deploy to your default region!

```
$ cdk deploy
```

## Useful commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation
