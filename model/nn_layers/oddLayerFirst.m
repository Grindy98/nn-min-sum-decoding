classdef oddLayerFirst < nnet.layer.Layer

    properties
        inLayerMask % E sparse matrix with indices of input var node conns
    end

    methods
        function layer = oddLayerFirst(name, tannerGraph)
            layer.NumInputs = 1;
            layer.Name = name;
            layer.InputNames = 'inLayerX';
            layer.NumOutputs = 1;
            layer = layer.initializeMasks(tannerGraph);
        end

        function Z = predict(layer, inLayerX)
            
            %  Mask layer input(no training for odd layer)
            Z = layer.inLayerMask*inLayerX;
        end

        function this = initializeMasks(this, tannerGraph)
            E = size(tannerGraph.Edges, 1); % number of neurons
            B = zeros(E,1);
            for i = 1:E
                currE = tannerGraph.Edges{i, 'EndNodes'};
                vNode = currE{1};
                
                % Store index of input node
                vNodeScan = textscan(vNode, "%c%u");
                B(i) = vNodeScan{2};
            end
            this.inLayerMask = ind2vec(B')';

        end

    end
end