
function plotTannerGraph(mat_in)
    mat = mat_in';
    G = getTannerGraph(mat_in);
    n_v = size(mat, 1);
    n_c = size(mat, 2);
    X = linspace(1,2, n_v);
    X = cat(2, X, linspace(1,2, n_c));
    Y = cat(1, zeros(n_v, 1), ones(n_c, 1));
    plot(G,'XData',X,'YData',Y)
end