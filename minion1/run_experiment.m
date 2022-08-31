% pe = pyenv('Version','/usr/bin/python3.9');

moduleName = 'TLLExperimentGroup20220831094716';
numCores = 1;

if count(py.sys.path,'') == 0
    insert(py.sys.path,int32(0),'');
end
translationModule = py.importlib.import_module(moduleName);

experCell = eval(strcat('py.', moduleName, '.f(py.str(pwd))'));
results = cell(size(experCell));
for ii = 1:numel(experCell)
    results{ii} = cell(size(experCell{ii}));
    for jj = 1:numel(results{ii})
        results{ii}{jj} = executeExperiment(experCell{ii}{jj},moduleName,numCores);
    end
end

