import numpy as np
import cdd
import TLLnet
import volestipy
import pickle
import sys
import datetime
import os
import tensorflow as tf
import importlib



def generatePolytope(dim,numGenerators=None,extents=[-2,2]):
    if numGenerators == None:
        numGenerators = dim
    if len(np.array(extents).shape) == 1:
        extents = np.vstack([extents for k in range(dim)]).tolist()
    extents = np.array(extents)
    
    matVrep = cdd.Matrix( \
            np.hstack( \
                [ \
                    np.ones((numGenerators,1)), \
                    np.random.uniform(low=extents[:,0].reshape((dim,1)), high=extents[:,1].reshape((dim,1)), size=(dim,numGenerators)).T \
                ] \
            ), \
            number_type='float'
        )
    matVrep.rep_type = cdd.RepType.GENERATOR
    matHrep = cdd.Polyhedron(matVrep).get_inequalities()
    can = matHrep.canonicalize()
    to_keep = sorted(list(frozenset(range(len(matHrep))) - can[1]))
    matHrep = np.array(matHrep)[to_keep]
    return {'A':matHrep[:,1:], 'b':-matHrep[:,0], 'numFaces':len(to_keep) ,'polyDefinition': 'Ax >= b'}

# Also applies a scaling to the polytope generated from the function above to vary the size (it is the same size or smaller)
def generateTLLProblem(n=1,N=2,M=None,m=1,numGenerators=10,extents=[-2,2],numSamples=1000):
    tllExample = TLLnet.TLLnet(input_dim=n,output_dim=m,linear_fns=N,uo_regions=M,incBias=True,flat=True)
    tllExample.generateRandomCPWA(scale=1)
    hasNaN = True
    while hasNaN:
        poly = generatePolytope(n,numGenerators,extents=extents)
        poly['numGenerators'] = numGenerators
        volPoly = volestipy.HPolytope(-1 * (1/(0.5*np.random.rand()+0.5)) * poly['A'], -poly['b'])
        inputSamples = np.array(volPoly.generate_samples(numSamples))
        outputSamples = np.array(tllExample.model.predict(inputSamples))
        hasNaN = ( np.count_nonzero(np.logical_not(np.isfinite(inputSamples))) > 0)
    problem = { \
            'n': n, \
            'N': N, \
            'M': M, \
            'm': m, \
            'TLLnetwork': tllExample.model, \
            'TLLparameters': { \
                    'localLinearFunctions': tllExample.getAllLocalLinFns(), \
                    'selectorMatrices':     tllExample.getAllSelectors() \
                }, \
            'inputPoly': poly, \
            'samples': { \
                    'input': inputSamples, \
                    'output': outputSamples \
                } \
        }
    return problem

# This function adds various path information to the dict, and then saves the result + hd5 model file
# to files in the base path (which defaults to baseName + date/time)
def generateTLLExperiment(instances,baseName='TLLExperiment',basePath=None):
    date_time = datetime.datetime.now().strftime('_%Y%m%d-%H%M%S')
    if basePath == None:
        basePath = './' + baseName + date_time
    basePath = basePath.rstrip('/')
    os.mkdir(basePath)
    for k in range(len(instances)):
        instances[k]['basePath'] = basePath
        instances[k]['baseName'] = baseName + '_instance_' + str(k).zfill(int(np.log10(len(instances))+1)) + date_time
        mynet = instances[k]['TLLnetwork']
        instances[k]['TLLnetwork'] = basePath + '/' + instances[k]['baseName'] + '.h5'
        mynet.save(instances[k]['TLLnetwork'])
    

def generateTLLExperimentFlat(instances,baseName='TLLExperiment',basePath=None,n=1,N=2,M=None,m=1,numGenerators=10,extents=[-2,2],numSamples=1000):
    date_time = datetime.datetime.now().strftime('_%Y%m%d-%H%M%S')
    if basePath == None:
        basePath = './' + baseName + date_time
    basePath = basePath.rstrip('/')
    os.mkdir(basePath)
    for k in range(len(instances)):
        instances[k]['basePath'] = basePath
        instances[k]['baseName'] = baseName + '_instance_' + str(k).zfill(int(np.log10(len(instances))+1)) + date_time
        instances[k]['TLLnetwork'] = basePath + '/' + instances[k]['baseName'] + '.h5'
        tllExample = 0
        tllExample = TLLnet.TLLnet(input_dim=n,output_dim=m,linear_fns=N,uo_regions=M,incBias=True,flat=True)
        tllExample.generateRandomCPWA(scale=1)
        hasNaN = True
        while hasNaN:
            poly = generatePolytope(n,numGenerators,extents=extents)
            poly['numGenerators'] = numGenerators
            volPoly = volestipy.HPolytope(-1 * (1/(0.5*np.random.rand()+0.5)) * poly['A'], -poly['b'])
            inputSamples = np.array(volPoly.generate_samples(numSamples))
            outputSamples = np.array(tllExample.model.predict(inputSamples))
            hasNaN = ( np.count_nonzero(np.logical_not(np.isfinite(inputSamples))) > 0)
        tllExample.model.save(instances[k]['TLLnetwork'])
        instances[k]['n'] = n
        instances[k]['N'] = N
        instances[k]['M'] = M
        instances[k]['m'] = m
        instances[k]['TLLparameters'] = { \
                'localLinearFunctions': tllExample.getAllLocalLinFns(), \
                'selectorMatrices':     tllExample.getAllSelectors() \
            }
        instances[k]['inputPoly'] = poly
        instances[k]['samples'] = { \
                'input': inputSamples, \
                'output': outputSamples \
            }
        tllExample = 0
        importlib.reload(tf)
        importlib.reload(TLLnet)

def addTLLAndPathToExisting(instances,baseName='TLLExperiment',basePath=None):
    date_time = datetime.datetime.now().strftime('_%Y%m%d-%H%M%S')
    if basePath == None:
        basePath = './' + baseName + date_time
    basePath = basePath.rstrip('/')
    os.mkdir(basePath)
    os.mkdir(os.path.join(basePath,baseName))
    for k in range(len(instances)):
        instances[k]['basePath'] = basePath
        instances[k]['baseName'] = baseName + '_instance_' + str(k).zfill(int(np.log10(len(instances))+1)) + date_time
        instances[k]['TLLnetwork'] = baseName + '/' + instances[k]['baseName'] + '.h5'
        temp = {}
        temp['localLinearFns'] = instances[k]['TLLparameters']['localLinearFunctions']
        for out in range(len(temp['localLinearFns'])):
            temp['localLinearFns'][out][0] = temp['localLinearFns'][out][0].T
        temp['selectorSets'] = [ [ TLLnet.selectorMatrixToSet(sMat) for sMat in sOutputs] for sOutputs in instances[k]['TLLparameters']['selectorMatrices'] ]
        temp['TLLFormatVersion'] = 1
        tllExample = TLLnet.TLLnet.fromTLLFormat(instances[k] | temp)
        tllExample.createKeras(incBias=True,flat=True)
        tllExample.model(tf.keras.Input((instances[k]['n'],)))
        tllExample.model.get_input_shape_at(0)
        tllExample.model.save(os.path.join(basePath,instances[k]['TLLnetwork']))
        tllExample = 0
        importlib.reload(tf)
        importlib.reload(TLLnet)



def saveAndGenerateMATLABInterface(experimentGroup,moduleName='TLLExperimentGroup'):
    if type(experimentGroup) != list or len(experimentGroup) == 0:
        print('Invalid experiment group')
        return
    for idx in range(len(experimentGroup)):
        if len(experimentGroup[idx]) > 0 and 'basePath' in experimentGroup[idx][0]:
            basePath = experimentGroup[idx][0]['basePath']
        else:
            print('Invalid problem group...')
            return
        date_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        moduleName = moduleName + date_time
        with open( os.path.join(  basePath ,  moduleName + '.p'),'wb') as fp:
            pickle.dump(experimentGroup,fp,protocol=pickle.HIGHEST_PROTOCOL)
        with open(os.path.join( basePath, moduleName + '.py' ),'wb') as fp:
            fp.write(b'\n\
import pickle\n\
def f(path=\'.\'):\n\
    with open(path.rstrip(\'/\')+\'/' + str.encode(moduleName) + b'.p\', \'rb\') as fp:\n\
        retVal = pickle.load(fp)\n\
    return retVal\n\
        \n')
        with open(os.path.join(basePath, 'run_experiment.m'),'w') as fp:
            print('% pe = pyenv(\'Version\',\'/usr/bin/python3.9\');\n\
\n\
moduleName = \'' + moduleName + '\';\n\
numCores = 1;\n\
\n\
if count(py.sys.path,\'\') == 0\n\
    insert(py.sys.path,int32(0),\'\');\n\
end\n\
translationModule = py.importlib.import_module(moduleName);\n\
\n\
experCell = eval(strcat(\'py.\', moduleName, \'.f(py.str(pwd))\'));\n\
\
results = cell(size(experCell));\n\
for ii = 1:numel(experCell)\n\
    results{ii} = cell(size(experCell{ii}));\n\
    for jj = 1:numel(results{ii})\n\
        results{ii}{jj} = executeExperiment(experCell{ii}{jj},moduleName,numCores);\n\
    end\n\
end\n\
', file=fp)
        os.popen('cp executeExperiment.m ' + basePath)
        with open(os.path.join(basePath, 'run_experiment.sh'), 'w') as fp:
            print('#!/bin/bash\n\
SCRIPT_DIR=$( cd -- \"$( dirname -- \"${BASH_SOURCE[0]}\" )\" &> /dev/null && pwd )\n\
cd \"$SCRIPT_DIR\"\n\
matlab -r run_experiment\n\
ssh 10.0.0.10 \"mkdir -p /media/azuredata/' + basePath + '\"\n\
scp ~/acc_code/' + basePath + ' 10.0.0.10:/media/azuredata/' + basePath + '\n\
pwsh ~/shutdown_self.ps1', file=fp)


if __name__=='__main__':

    # mytll = TLLnet(input_dim=2,linear_fns=7,uo_regions=20)

    # mat = mytll.selectorMatFromSet(frozenset([1,5,6]))

    # print(mat)

    # mytll.generateRandomCPWA()

    # print(mytll.getLocalLinFns())

#     poly = generatePolytope(2,20)

#     # print(poly)

#     with open('testFile' + str(1).zfill(5) + '.p','wb') as fp:
#         pickle.dump([poly,2],fp,protocol=pickle.HIGHEST_PROTOCOL)
    
#     with open('testFileModule' + str(1).zfill(5) + '.py','wb') as fp:
#         fp.write(b'\n\
# import pickle\n\
# def f(path):\n\
#     with open(path+\'/testFile00001.p\', \'rb\') as fp:\n\
#         retVal = pickle.load(fp)\n\
#     return retVal\n\
#         \n')


    # # PROBLEM LIST 0
    # idx = 0
    # for k in range(len(problemList[idx])):
    #     problemList[idx][k] = generateTLLProblem(n=1,m=1,N=100,M=60)
    # generateTLLExperiment(problemList[idx],baseName='TLLexper_n1m1N100M60_')
    # print('Done with PROBLEM LIST 0')

    with open('sizeVsTime_n2_input.p','rb') as fp:
        originalExperiment = pickle.load(fp)

    problemList = []
    for jj in range(2):
        for ii in range(1):
            problemList.append([originalExperiment[jj][ii]])
    
    for idx in range(len(problemList)):
        addTLLAndPathToExisting(problemList[idx],basePath='minion' + str(idx))


    # Generate a list for this problem group:
    # problemList = [[{} for k in range(50)] for i in range(4)]

    # # PROBLEM LIST 0
    # idx = 0
    # generateTLLExperimentFlat(problemList[idx],baseName='TLLexper_n1m1N32M32_',n=1,m=1,N=32,M=32)
    # print('Done with PROBLEM LIST 0')

    # # PROBLEM LIST 0
    # idx = 1
    # generateTLLExperimentFlat(problemList[idx],baseName='TLLexper_n1m1N64M48_',n=1,m=1,N=64,M=48)
    # print('Done with PROBLEM LIST 0')

    # # PROBLEM LIST 0
    # idx = 2
    # generateTLLExperimentFlat(problemList[idx],baseName='TLLexper_n2m1N32M32_',n=2,m=1,N=32,M=32)
    # print('Done with PROBLEM LIST 0')

    # # PROBLEM LIST 0
    # idx = 3
    # generateTLLExperimentFlat(problemList[idx],baseName='TLLexper_n2m1N64M48_',n=2,m=1,N=64,M=48)
    # print('Done with PROBLEM LIST 0')

    # # PROBLEM LIST 1
    # idx = 1
    # for k in range(len(problemList[idx])):
    #     problemList[idx][k] = generateTLLProblem(n=2,m=1,N=15,M=40)
    # generateTLLExperiment(problemList[idx],baseName='TLLexper_n2m1N15M40_')
    # print('Done with PROBLEM LIST 1')

    # # PROBLEM LIST 2
    # idx = 2
    # for k in range(len(problemList[idx])):
    #     problemList[idx][k] = generateTLLProblem(n=2,m=1,N=128,M=100)
    # generateTLLExperiment(problemList[idx],baseName='TLLexper_n2m1N128M100_')
    # print('Done with PROBLEM LIST 2')

    # Create a MATLAB interface for this problem group:
    for idx in range(len(problemList)):
        saveAndGenerateMATLABInterface([problemList[idx]])

    pass