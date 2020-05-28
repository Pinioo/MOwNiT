f1 = @(x) exp(-x.^2).*log(x).^2;
f2 = @(x) 1./(x.^3 - 2.*x - 5);
f3 = @(x) (x.^5).*exp(-x).*sin(x);
f4 = @(x,y) 1./(sqrt(x + y).*(1 + x + y));
f5 = @(x,y) x.^2 + y.^2;

x_min = 0.01;
x_max = 2;
x = linspace(x_min, x_max, 101);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
y1 = f1(x);

quad1 = quad(f1, x_min, x_max);
simp1 = simpson(x, y1);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
y2 = f2(x);

quad2 = quad(f2,x_min,x_max);
simp2 = simpson(x,y2);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
y3 = f3(x);

quad3 = quad(f3,x_min,x_max);
simp3 = simpson(x,y3);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
[~, errs1] = simp_comp(f1, x_min, x_max, 101);
[~, errs2] = simp_comp(f2, x_min, x_max, 101);
[ns, errs3] = simp_comp(f3, x_min, x_max, 101);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
digits(10);
f4_tiled = vpa(integral2(f4,0,1,0,@(x) 1-x, 'Method', 'tiled'));
f4_iterated = vpa(integral2(f4,0,1,0,@(x) 1-x, 'Method', 'iterated'));
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
xs = linspace(-3,3,100);
ys = linspace(-5,5,100);

[n, e] = trapz_acc(f5, 400, 5000);
matlab_inacc = abs(680-integral2(f5, -3, 3, -5, 5))
trapz_inacc = e(end)

function integ = simpson(x,y)
    h = x(2) - x(1);
    integ = (h/3).*(y(1) + 4.*sum(y(2:2:end-1)) + 2.*sum(y(3:2:end-2)) + y(end));
end

function [ns, errs] = simp_comp(f, x_min, x_max, n_max)
    ns = 3:2:n_max;
    errs = zeros(1,length(ns));
    q = quad(f, x_min, x_max);
    diff = @(s) abs(q-s);
    for i = 1:length(ns)
        xs = linspace(x_min,x_max,ns(i));
        ys = f(xs);
        simp = simpson(xs, ys);
        errs(i) = diff(simp);
    end
end

function integ = trapzdbl(xs, ys, Z)
    integ = trapz(ys, trapz(xs, Z, 2));
end

function [ns, trs] = trapz_acc(f, n_min, n_max)
    ns = n_min:100:n_max;
    trs = zeros(1,length(ns));
    diff = @(s) abs(680 - s);
    for i = 1:length(ns)  
        xs = linspace(-3, 3, ns(i));
        ys = linspace(-5, 5, ns(i));
        [X, Y] = meshgrid(xs, ys);
        Z = f(X, Y);
        trs(i) = diff(trapzdbl(xs, ys, Z));
    end
end