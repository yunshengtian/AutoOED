float* evaluate_objective(float* x) {
    static float y[2] = {};
    y[0] = x[0];
    y[1] = x[1];
    return y;
}