classdef oddLayer < nnet.layer.Layer

    properties
        prevLayerMask % ExE adjacency matrix defining prev layer conns
        inLayerMask % E sparse matrix with indices of input var node conns
    end

    methods
        function layer = oddLayer(name, tannerGraph)
            layer.NumInputs = 2;
            layer.Name = name;
            layer.InputNames = {'prevLayerX', 'inLayerX'};
            layer.NumOutputs = 1;
            layer = layer.initializeMasks(tannerGraph);
        end

        function Z = predict(layer, prevLayerX, inLayerX)
            
            %  Mask layer inputs and sum them (no training for odd layer)
            Z = layer.prevLayerMask*prevLayerX + ...
                layer.inLayerMask*inLayerX;
        end

        function this = initializeMasks(this, tannerGraph)
            E = size(tannerGraph.Edges, 1); % number of neurons
            A = zeros(E);
            B = zeros(E,1);
            for i = 1:E
                % For every neuron, generate a row vector representing 
                % connections to previous layer, and form a matrix
            
                % All other edges sharing same v-node with ith edge
                currE = tannerGraph.Edges{i, 'EndNodes'};
                vNode = currE{1};
                outEdgeInd = outedges(tannerGraph, vNode);
                % Fill vector with corresp indices as 1
                mask = zeros(E, 1);
                mask(outEdgeInd) = 1;
                % Force clear bit corresp to the current edge
                mask(i) = 0;
                A(i,:) = mask;
            
                % Store index of input node
                vNodeScan = textscan(vNode, "%c%u");
                B(i) = vNodeScan{2};
            end
            this.prevLayerMask = A;
            this.inLayerMask = ind2vec(B')';

        end

    end
end