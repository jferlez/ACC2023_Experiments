function reachResult = executeExperiment(exper, moduleName, numCores)

nValid = 10;

n = double(exper{'n'});
N = double(exper{'N'});
m = double(exper{'m'});
M = double(exper{'M'});
tllFile = char(string(exper{'TLLnetwork'}));
A = double(exper{'inputPoly'}{'A'});
b = double(exper{'inputPoly'}{'b'})';
inSamples = double(exper{'samples'}{'input'});
outSamples = double(exper{'samples'}{'output'});
basePath = char(string(exper{'basePath'}));
baseName = char(string(exper{'baseName'}));

inputPoly = Polyhedron(-A,-b).minHRep;
inputStar = Conversion.toStar(inputPoly);
% The conversion from Polyhedron doesn't set predicate_lb/ub, and this will
% cause problems with the star set later. We have kept everything bounded
% on purpose, so [-10,10] will work as coordinate-wise bounds (actually,
% [-2,2] would probably work just as well)
inputStar.predicate_lb = -10*ones(n, 1);
inputStar.predicate_ub = 10*ones(n,1);

disp('********************************************************************************');
disp('********************************************************************************');
disp('*****                                                                      *****');
dStr = ['Working on ' baseName];
dStrLen = floor((70-size(dStr,2))/2);
dStr = pad(dStr,dStrLen+size(dStr,2),'left');
dStr = pad(dStr,70,'right');
disp(['*****' dStr '*****']);
disp('*****                                                                      *****');
disp('********************************************************************************');
disp('********************************************************************************');

reachResult.nn = Load_nn(tllFile);

reachResult.validationInputs = inSamples(1:nValid,:)';
reachResult.validationOutputs = ones(m,nValid);
for ii = 1:nValid
    reachResult.validationOutputs(:,ii) = reachResult.nn.evaluate(reachResult.validationInputs(:,ii));
end

if numCores > 1
    reachResult.nn.start_pool(numCores);
end
% tic;
% reachResult.reachStar = reachResult.nn.reach(inputStar,'approx-star',numCores);
% reachResult.time = toc;
% reachResult.reachBox = reachResult.reachStar.getBox();
% reachResult.lb = reachResult.reachBox.lb;
% reachResult.ub = reachResult.reachBox.ub;


Ts = 0.01;
A = double(exper{'system'}{'A'});
B = double(exper{'system'}{'B'});
sz  = size(A);
n = sz(1);
sz = size(B);
m = sz(2);
C = eye(n);
D = zeros(n,m);

NN_Controller = reachResult.nn; % feedforward neural network controller
Plant = DLinearODE(A, B, C, D, Ts);
feedbackMap = [0]; % feedback map, y[k] 

ncs = NNCS(NN_Controller, Plant, feedbackMap); % the neural network control system

args.numSteps = 2;
args.numCores = 1;
args.ref_input = [];
args.reachMethod = 'approx-star';
args.init_set = inputStar;

tic;
[P1, reachTime1] = ncs.reach(args);
reachResult.time = toc;
reachResult.reachStars = P1;
reachResult.reachBoxes = {};
reachResult.reachBounds = {};
for ii = 1:length(P1)
    reachResult.reachBoxes{ii} = reachResult.reachStars(ii).getBox();
    reachResult.reachBounds{ii} = [reachResult.reachBoxes{ii}.lb; reachResult.reachBoxes{ii}.ub];
end
mkdir('mat_results')
save(['mat_results/' baseName '.mat'],'reachResult');

for ii = 1:length(reachResult.reachBoxes)
    h5create([moduleName '.h5'],['/' baseName '/lb_T=' num2str(ii)],size(reachResult.reachBoxes{ii}.lb));
    h5write([moduleName '.h5'],['/' baseName '/lb_T=' num2str(ii)],reachResult.reachBoxes{ii}.lb);
    h5create([moduleName '.h5'],['/' baseName '/ub_T=' num2str(ii)],size(reachResult.reachBoxes{ii}.ub));
    h5write([moduleName '.h5'],['/' baseName '/ub_T=' num2str(ii)],reachResult.reachBoxes{ii}.ub);
end
h5create([moduleName '.h5'],['/' baseName '/timeElapsed'],[1 1]);
h5write([moduleName '.h5'],['/' baseName '/timeElapsed'],reachResult.time);
h5create([moduleName '.h5'],['/' baseName '/validationInputs'],size(reachResult.validationInputs));
h5write([moduleName '.h5'],['/' baseName '/validationInputs'],reachResult.validationInputs);
h5create([moduleName '.h5'],['/' baseName '/validationOutputs'],size(reachResult.validationOutputs));
h5write([moduleName '.h5'],['/' baseName '/validationOutputs'],reachResult.validationOutputs);

disp('================================================================================');
disp(' ');
disp(['Finished ' baseName]);
disp(['Elapsed time: ' char(string(reachResult.time)) ' seconds']);
disp(' ');
disp('================================================================================');
disp(' ');
disp(' ');
disp(' ');
disp(' ');
disp(' ');

