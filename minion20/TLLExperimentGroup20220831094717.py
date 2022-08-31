
import pickle
def f(path='.'):
    with open(path.rstrip('/')+'/TLLExperimentGroup20220831094717.p', 'rb') as fp:
        retVal = pickle.load(fp)
    return retVal
        
