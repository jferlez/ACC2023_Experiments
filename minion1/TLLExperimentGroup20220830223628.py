
import pickle
def f(path='.'):
    with open(path.rstrip('/')+'/TLLExperimentGroup20220830223628.p', 'rb') as fp:
        retVal = pickle.load(fp)
    return retVal
        
