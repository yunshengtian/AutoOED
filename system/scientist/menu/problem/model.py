from autooed.problem.common import load_yaml_problem, save_yaml_problem, remove_yaml_problem


class MenuProblemModel:

    def load_problem(self, name):
        return load_yaml_problem(name)

    def save_problem(self, problem_cfg):
        return save_yaml_problem(problem_cfg)

    def remove_problem(self, name):
        return remove_yaml_problem(name)
