
import numpy as np
import pickle
import os
import sys
import re
import h5py

if __name__ == '__main__':
    
    resultsDir = os.path.abspath( \
            os.path.join( \
                os.path.dirname( os.path.abspath(sys.argv[0]) ),
                '..', \
                'results/nnv' \
            ) \
        )
    resultsOutputFile = os.path.join(resultsDir,'results_nnv.p')
    
    baseName = 'minion'
    experGroupName = 'TLLExperimentGroup'

    dirList = [ \
            'nnv_3step_20220905', \
            'nnv_3step_large_20220902' \
        ]
    numExperimentsPerGroup = 10
    results = {}

    for d in dirList:
        r = os.path.join(resultsDir, d)
        if not os.path.isdir(r):
            print(f'ERROR: {d} is not a valid directory... skipping...')
            continue
        
        workerContents = os.listdir(r)

        for pname in workerContents:
            checkName = re.match(r'^' + baseName + r'([0-9]+)$', os.path.basename(pname))
            if not os.path.isdir(os.path.join(r,pname)) or not checkName or not os.path.isdir(os.path.join(r,pname,pname)):
                continue
            workerIdx = int(checkName.group(1))
            sizeIdx = workerIdx // numExperimentsPerGroup
            experIdx = workerIdx % numExperimentsPerGroup
            if not sizeIdx in results:
                results[sizeIdx] = {}
            if experIdx in results[sizeIdx]:
                print('ERROR: duplicate experiment in experiment group...')
                exit(1)
            results[sizeIdx][experIdx] = {}
            results[sizeIdx][experIdx]['reachNNV'] = {}

            contents = os.listdir(os.path.join(r,pname,pname))
            resultsFile = None
            for fname in contents:
                if re.match(r'^' + experGroupName + r'.*\.h5$',os.path.basename(os.path.join(r,pname,pname,fname))):
                    resultsFile = os.path.join(r,pname,pname,fname)
                    break
            
            if resultsFile is None:
                print(f'ERROR: no matching .h5 file in {os.path.join(r,pname)}')
                logFile = None
                numSteps = None
                for fname in contents:
                    if fname == 'log.out' and os.path.isfile(os.path.join(r,pname,pname,'log.out')):
                        logFile = os.path.join(r,pname,pname,'log.out')
                        with open(logFile) as fp:
                            log = fp.readlines()
                        numSteps = 0
                        for ln in log:
                            if re.search('plant',ln):
                                numSteps += 1
                        results[sizeIdx][experIdx]['reachNNV']['numSteps'] = numSteps
                        results[sizeIdx][experIdx]['reachNNV']['incomplete'] = True
                if logFile is None:
                    print(f'ERROR: No log file found in {os.path.join(r,pname)}')
                    continue
            else:
                temp = {}
                timeElapsed = -1.0
                dataFile = h5py.File(resultsFile,'r')
                inst = list(dataFile.keys())[0]
                dataLabels = dataFile[inst].keys()
                maxTime = -1
                for ptr in dataLabels:
                    bdData = re.match(r'(lb|ub)_T=([0-9]+)',ptr)
                    if bdData:
                        t = int(bdData.group(2))
                        maxTime = (t if t > maxTime else maxTime)
                        bd = np.array(dataFile[inst][ptr])
                        if not t in temp:
                            temp[t] = {'box':np.full((max(bd.shape),2),np.inf,dtype=np.float64),'time':0.0}
                        temp[t]['box'][:, (0 if bdData.group(1) == 'lb' else 1)] = bd.flatten()
                    elif ptr in ['timeElapsed', 'validationInputs', 'validationOutputs']:
                        temp[ptr] = np.array(dataFile[inst][ptr])
                    else:
                        print(f'ERROR: unexpected dataset {ptr}')
                if 'timeElapsed' in temp and maxTime >= 0:
                    temp[maxTime]['time'] = temp['timeElapsed'].flatten()[0]
                    temp['timeElapsed'] = temp['timeElapsed'].flatten()[0]
                if maxTime >= 0:
                    temp['numSteps'] = maxTime
                results[sizeIdx][experIdx]['reachNNV'] = temp
                results[sizeIdx][experIdx]['reachNNV']['valid'] = True
                dataFile.close()

            # print(results[sizeIdx][experIdx]['reachNNV'])
            # print(f'{baseName}{workerIdx} --> [{sizeIdx}][{experIdx}] --> {resultsFile}')
    with open(resultsOutputFile,'wb') as fp:
        pickle.dump(results, fp)
        