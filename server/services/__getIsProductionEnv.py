import os


def getIsProductionEnv():
    if os.getenv('ENVIRONMENT') in ['localprod', 'cloudprod']:
        return True
    elif os.getenv('ENVIRONMENT') in ['clouddev', 'localdev']:
        return False
    else:
        raise Exception("Invalid environment: " + os.getenv('ENVIRONMENT'))
