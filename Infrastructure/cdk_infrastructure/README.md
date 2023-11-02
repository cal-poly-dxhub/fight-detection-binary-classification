
# Inference Infrastructure CDK Stack

### Using Node v16.3.0

## **Files / Folders**

### **lambda:**
* Contains lambda_handler (lambda_handler.py) that calls model / runs inference
* STACK DOES NOT START MODEL RUNNING AUTOMATICALLY

### **General Notes on Inference Stack**
* Depends on hardcoded rekognition model arn 
* Resources in stack: 
    * s3: upload bucket
    * trigger: triggers lambda invocation on upload
    * lambda: runs inference for each frame uploaded
    * dynamoDB: keeps track of each current window for each camera
    * sns: publishes fight alert 
* automatically adds code to lambda and sets up permissions / roles
* NOTE: CDK SPINS UP AN EXTRA LAMBDA FUNCTION AS INTERMEDIARY FOR TRIGGER
    * Due to a circular dependency between s3 bucket and lambda function when creating trigger there is no way to avoid this programatically.
    * To solve this, delete the trigger and re-setup s3 trigger on upload manually in console



--------------- Every below is autogenerated cdk readme ---------------



The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!