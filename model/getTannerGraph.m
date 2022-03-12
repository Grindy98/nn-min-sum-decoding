function g=getTannerGraph(mat_in)
    mat = mat_in';
    n_v = size(mat, 1);
    n_c = size(mat, 2);
    n_nodes = n_v + n_c;
    A = zeros(n_nodes);
    for i = 1:n_nodes
        for j = 1:n_nodes
            flag = 0;
            i_orig = i;
            j_orig = j;
            if i_orig > n_v
                i_orig = i_orig - n_v;
                flag = xor(flag, 1);
            end
            if j_orig > n_v
                j_orig = j_orig - n_v;
                flag = xor(flag, 1);
            end 
            if i_orig < j_orig
                [j_orig, i_orig] = deal(i_orig, j_orig);
            end
            if flag && mat(i_orig, j_orig)
                A(i, j) = 1;
            end
        end
    end
    type = [repmat("v", 1, n_v) repmat("c", 1, n_c)];
    idx = [(1:n_v) (1:n_c)];
    names = type + idx;
    g = graph(A, table(type', idx', names','VariableNames',{'Type', 'Index', 'Name'}));

end