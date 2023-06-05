import json
import sys

import cplex
from cplex.exceptions import CplexError


def parse_mps(filepath: str):
    file1 = open(filepath)
    lines = file1.readlines()

    rhs = []
    lo_bounds = []
    up_bounds = []
    variables_names = []
    const_names = []
    types = ""
    senses = ""
    now_parsing = ""
    obj_sense = "MIN"

    const_var_values = {}
    vars = {}
    obj = []
    obj_name = ""

    marker_session = "C"

    variable_name = "x"
    constraint_name = "r"

    counter_constraints = 0
    counter_variables = 0

    map_variables = {}
    map_constraints = {}
    for line in lines:
        if line.startswith("OBJSENSE"):
            now_parsing = "OBJSENSE"

        if line.startswith("ROWS"):
            now_parsing = "ROWS"

        if line.startswith("COLUMNS"):
            now_parsing = "COLUMNS"

        if line.startswith("RHS"):
            now_parsing = "RHS"

        if line.startswith("BOUNDS"):
            now_parsing = "BOUNDS"

        if line.startswith("ENDATA"):
            now_parsing = "ENDATA"

        if now_parsing == "OBJSENSE" and not line.startswith("OBJSENSE"):
            fields = line.split()
            obj_sense = fields[0]

        if now_parsing == "ROWS" and not line.startswith("ROWS"):
            if line.split()[0] != "N":
                counter_constraints += 1
                name_constraint = line.split()[1]
                map_constraints[name_constraint] = constraint_name + str(counter_constraints)

                senses = senses + (line.split()[0])
                const_var_values[map_constraints[name_constraint]] = {"variables": [],
                                                                      "values": [],
                                                                      "rhs": 0.00,
                                                                      }
                const_names.append(map_constraints[name_constraint])

            elif line.split()[0] == "N":
                obj_name = line.split()[1]

        if now_parsing == "COLUMNS" and not line.startswith("COLUMNS"):
            fields = line.split()
            name_variable = fields[0]
            if fields[0] not in map_variables.keys() and fields[0] != "MARK0000" and fields[0] != "MARK0001":
                counter_variables += 1
                map_variables[name_variable] = variable_name + str(counter_variables)
                var_index: str = map_variables[name_variable]

            if fields[0] != "MARK0000" and fields[0] != "MARK0001":
                if var_index not in vars:
                    vars[var_index] = {"constraint_names": [],
                                            "constraint_values": [],
                                            "lower_bound": 0.00,
                                            "upper_bound": cplex.infinity,
                                            "type": "C",
                                            obj_name: 0.00}

            for index, field in enumerate(fields):
                if index != 0 and index % 2 != 0 and field != "'MARKER'" and field != obj_name:
                    constraint_index = map_constraints[fields[index]]
                    if constraint_index in const_var_values.keys():
                        constraint_index = map_constraints[fields[index]]
                        const_var_values[constraint_index]["variables"].append(var_index)
                        const_var_values[constraint_index]["values"].append(float(fields[index + 1]))
                        vars[var_index]["constraint_names"].append(constraint_index)
                        vars[var_index]["constraint_values"].append(float(fields[index + 1]))

                if index % 2 != 0 and field == obj_name:
                    vars[var_index].update({obj_name: fields[index + 1]})

            if fields[2] == "'INTORG'":
                marker_session = "I"

            elif fields[2] == "'INTEND'":
                marker_session = "C"

            if marker_session == "C" and fields[1] != "'MARKER'":
                vars[map_variables[fields[0]]].update({"lower_bound": float(0.00),
                                                            "upper_bound": cplex.infinity,
                                                            "type": "C"})

            elif marker_session == "I" and fields[1] != "'MARKER'":
                vars[map_variables[fields[0]]].update({"lower_bound": float(0.00),
                                                            "upper_bound": cplex.infinity,
                                                            "type": "I"
                                                            })

        if now_parsing == "RHS" and not line.startswith("RHS"):
            fields = line.split()

            for index, field in enumerate(fields):
                if index != 0:
                    if index % 2 != 0:
                        const_var_values[map_constraints[field]].update({"rhs": float(fields[index + 1])})

        if now_parsing == "BOUNDS" and not line.startswith("BOUNDS"):

            fields = line.split()

            var_index = map_variables[fields[2]]
            if fields[0] == "LO":
                vars[var_index].update({"lower_bound": float(fields[3])})

            if fields[0] == "UP":
                vars[var_index].update({"upper_bound": float(fields[3])})

            if fields[0] == "FX":
                vars[var_index].update({"lower_bound": float(fields[3]),
                                             "upper_bound": float(fields[3])})

            if fields[0] == "FR":
                vars[var_index].update({"lower_bound": -cplex.infinity,
                                             "upper_bound": cplex.infinity})

            if fields[0] == "MI":
                vars[var_index].update({"lower_bound": -cplex.infinity})

            if fields[0] == "PL":
                vars[var_index].update({"lower_bound": cplex.infinity})

            if fields[0] == "BV":
                vars[var_index].update({"type": "I"})

            if fields[0] == "LI":
                vars[var_index].update({"lower_bound": float(fields[3]),
                                             "type": "I"})

            if fields[0] == "UI":
                vars[var_index].update({"upper_bound": float(fields[3]),
                                             "type": "I"})

            if fields[0] == "SC":
                vars[var_index].update({"lower_bound": float(fields[3]),
                                             "type": "I"})

            if fields[0] == "SI":
                vars[var_index].update({"upper_bound": float(fields[3])})

    with open("json-tests/constraints.json", "w") as outfile:
        json.dump(const_var_values, outfile, indent=4)

    with open("json-tests/variables.json", "w") as outfile:
        json.dump(vars, outfile, indent=4)

    with open("json-tests/const_maps.json", "w") as outfile:
        json.dump(map_constraints, outfile, indent=4)

    with open("json-tests/var_maps.json", "w") as outfile:
        json.dump(map_variables, outfile, indent=4)

    for variable in vars.items():
        lo_bounds.append(variable[1]["lower_bound"])
        up_bounds.append(variable[1]["upper_bound"])
        types = types + variable[1]["type"]
        obj.append(float(variable[1][obj_name]))
        variables_names.append(variable[0])

    for constraints_var_n_value in const_var_values.items():
        rhs.append(constraints_var_n_value[1]["rhs"])

    return rhs, vars, lo_bounds, up_bounds, variables_names, const_names, senses, const_var_values, types, obj, obj_sense


def populate_by_row(prob, filepath: str):
    rows = []
    rhs, variables, lower_bounds, upper_bounds, variables_names, const_names, senses, const_var_values, types, obj, obj_sense = parse_mps(
        filepath)
    for constraint in const_var_values.items():
        rows.append([constraint[1]["variables"], constraint[1]["values"]])

    if obj_sense == "MIN":
        prob.objective.set_sense(prob.objective.sense.minimize)
    else:
        prob.objective.set_sense(prob.objective.sense.maximize)

    prob.variables.add(obj=obj, lb=lower_bounds, ub=upper_bounds,
                       types=types, names=variables_names)

    prob.linear_constraints.add(lin_expr=rows, senses=senses,
                                rhs=rhs, names=const_names)


def populate_by_col(prob, filepath: str):
    columns = []
    rhs, variables, lower_bounds, upper_bounds, variables_names, constraints_names, senses, constraints_var_n_values, types, obj, obj_sense = parse_mps(
        filepath)
    if obj_sense == "MIN":
        prob.objective.set_sense(prob.objective.sense.minimize)
    else:
        prob.objective.set_sense(prob.objective.sense.maximize)

    prob.linear_constraints.add(senses=senses,
                                rhs=rhs, names=constraints_names)

    for variable in variables.items():
        columns.append([variable[1]["constraint_names"], variable[1]["constraint_values"]])

    prob.variables.add(obj=obj, lb=lower_bounds, ub=upper_bounds,
                       names=variables_names, types=types, columns=columns)


def populate_by_non_zero(prob, filepath: str):
    aux = []
    vars_values_aux = []
    vals = []
    rows = []
    cols = []

    rhs, variables, lower_bounds, upper_bounds, variables_names, constraints_names, senses, constraints_var_n_values, types, obj, obj_sense = parse_mps(
        filepath)
    for constraint in constraints_var_n_values.items():
        aux.append(constraint[1]["variables"])

    for constraint in constraints_var_n_values.items():
        vars_values_aux.append(constraint[1]["values"])

    for index, vars in enumerate(aux):
        for var in vars:
            rows.append(index)
            cols.append(list(variables).index(var))

    for var_val in vars_values_aux:
        for vv in var_val:
            vals.append(vv)

    if obj_sense == "MIN":
        prob.objective.set_sense(prob.objective.sense.minimize)
    else:
        prob.objective.set_sense(prob.objective.sense.maximize)

    prob.linear_constraints.add(senses=senses, rhs=rhs, names=constraints_names)

    prob.variables.add(obj=obj, lb=lower_bounds, ub=upper_bounds, names=variables_names, types=types)

    prob.linear_constraints.set_coefficients(zip(rows, cols, vals))


def mipex1(pop_method, filepath):
    print(filepath)
    try:
        my_prob = cplex.Cplex()

        if pop_method == "r":
            print("Populating by row")
            populate_by_row(my_prob, filepath)

        elif pop_method == "c":
            print("Populating by col")
            populate_by_col(my_prob, filepath)

        elif pop_method == "n":
            print("Populating by non zero")
            populate_by_non_zero(my_prob, filepath)

        else:
            raise ValueError('pop_method must be one of "r", "c" or "n"')

        my_prob.solve()
    except CplexError as exc:
        print(exc)
        return

    print()
    print("Solution status = ", my_prob.solution.get_status(), ":", end=' ')
    # print(my_prob.solution.status[my_prob.solution.get_status()])
    print("Solution value  = ", my_prob.solution.get_objective_value())

    numcols = my_prob.variables.get_num()
    numrows = my_prob.linear_constraints.get_num()

    slack = my_prob.solution.get_linear_slacks()
    x = my_prob.solution.get_values()
    #
    # for j in range(numrows):
    #     print("Row %d:  Slack = %10f" % (j, slack[j]))
    # for j in range(numcols):
    #     print("Column %d:  Value = %10f" % (j, x[j]))

    print("Solution value  = ", my_prob.solution.get_objective_value())


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ["-r", "-c", "-n"]:
        print("Usage: main.py -X")
        print("   where X is one of the following options:")
        print("      r          generate problem by row")
        print("      c          generate problem by column")
        print("      n          generate problem by nonzero")
        print(" Exiting...")
        sys.exit(-1)
    mipex1(sys.argv[1][1], sys.argv[2])
