import json
import cplex
from cplex.exceptions import CplexError
import sys

file1 = open('simple.mps')
lines = file1.readlines()

def parse_mps_v2():

    rhs = []
    lower_bounds = []
    upper_bounds = []
    variables_names = []
    constraints_names = []
    types = ""
    senses = ""
    reading_now = ""

    constraints_var_n_values = {}
    variables = {}
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
        if line.startswith("ROWS"):
            reading_now = "ROWS"

        if line.startswith("COLUMNS"):
            reading_now = "COLUMNS"

        if line.startswith("RHS"):
            reading_now = "RHS"

        if line.startswith("BOUNDS"):
            reading_now = "BOUNDS"

        if line.startswith("ENDATA"):
            reading_now = "ENDATA"

        if reading_now == "ROWS" and not line.startswith("ROWS"):
            if line.split()[0] != "N":
                counter_constraints += 1
                name_constraint = line.split()[1]
                map_constraints[name_constraint] = constraint_name + str(counter_constraints)

                senses = senses + (line.split()[0])
                constraints_var_n_values[map_constraints[name_constraint]] = {"variables": [],
                                                             "values": [],
                                                             "rhs": 0.00,
                                                             }
                constraints_names.append(map_constraints[name_constraint])

            elif line.split()[0] == "N":
                obj_name = line.split()[1]



        if reading_now == "COLUMNS" and not line.startswith("COLUMNS"):
            fields = line.split()
            name_variable = fields[0]
            if fields[0] not in map_variables.keys() and fields[0] != "MARK0000" and fields[0] != "MARK0001":
                counter_variables += 1
                map_variables[name_variable] = variable_name + str(counter_variables)
                var_index = map_variables[name_variable]

            if fields[0] != "MARK0000" and fields[0] != "MARK0001":
                if var_index not in variables:
                    print("ora creo variabile" + map_variables[name_variable] )
                    variables[var_index] = {"constraint_names": [],
                                            "constraint_values": [],
                                            "lower_bound": 0.00,
                                            "upper_bound": cplex.infinity,
                                            "type": "C",
                                            obj_name: 0.00}

            for index, field in enumerate(fields):
                    if index != 0 and index % 2 != 0 and field != "'MARKER'" and field != obj_name:
                        constraint_index = map_constraints[fields[index]]
                        if constraint_index in constraints_var_n_values.keys():
                            constraint_index = map_constraints[fields[index]]
                            constraints_var_n_values[constraint_index]["variables"].append(var_index)
                            constraints_var_n_values[constraint_index]["values"].append(float(fields[index+1]))
                            variables[var_index]["constraint_names"].append(constraint_index)
                            variables[var_index]["constraint_values"].append(float(fields[index + 1]))


                    if index%2 != 0 and field == obj_name:
                        variables[var_index].update({obj_name: fields[index+1]})

            if fields[0] == "MARK0000":
                    marker_session = "I"

            elif fields[0] == "MARK00000":
                    marker_session = "C"

            if marker_session == "C" and fields[1] != "'MARKER'":
                variables[map_variables[fields[0]]].update( {"lower_bound": float(0.00),
                                        "upper_bound": cplex.infinity,
                                        "type": "C"})

            elif marker_session == "I" and fields[1] != "'MARKER'":
                variables[map_variables[fields[0]]].update({"lower_bound": float(0.00),
                                        "upper_bound": cplex.infinity,
                                        "type": "I"
                                       })


        if reading_now == "RHS" and not line.startswith("RHS"):
            fields = line.split()

            for index, field in enumerate(fields):
                if index!=0:
                    if index%2 != 0:
                        constraints_var_n_values[map_constraints[field]].update({"rhs": float(fields[index+1])})


        if reading_now == "BOUNDS" and not line.startswith("BOUNDS"):

            fields = line.split()

            var_index = map_variables[fields[2]]
            if fields[0] == "LO":
                variables[var_index].update({"lower_bound": float(fields[3])})

            if fields[0] == "UP":
                variables[var_index].update({"upper_bound": float(fields[3])})

            if fields[0] == "FX":
                variables[var_index].update({"lower_bound": float(fields[3]),
                                             "upper_bound": float(fields[3])})

            if fields[0] == "FR":
                variables[var_index].update({"lower_bound": -cplex.infinity,
                                        "upper_bound": cplex.infinity})

            if fields[0] == "MI":
                variables[var_index].update({"lower_bound": -cplex.infinity})

            if fields[0] == "PL":
                variables[var_index].update({"lower_bound": cplex.infinity})

            if fields[0] == "BV":
                print("")

            if fields[0] == "LI":
                variables[var_index].update({"lower_bound": float(fields[3])})


            if fields[0] == "UI":
                variables[var_index].update({"upper_bound": float(fields[3])})


            if fields[0] == "SC":
                variables[var_index].update({"lower_bound": float(fields[3])})


            if fields[0] == "SI":
                variables[var_index].update({"upper_bound": float(fields[3])})



    with open("constraints.json", "w") as outfile:
       json.dump(constraints_var_n_values, outfile, indent=4)

    with open("variables.json", "w") as outfile:
       json.dump(variables, outfile, indent=4)

    with open("const_maps.json", "w") as outfile:
        json.dump(map_constraints, outfile, indent=4)

    with open("var_maps.json", "w") as outfile:
        json.dump(map_variables, outfile, indent=4)

    for variable in variables.items():
        lower_bounds.append(variable[1]["lower_bound"])
        upper_bounds.append(variable[1]["upper_bound"])
        types = types + variable[1]["type"]
        obj.append(float(variable[1][obj_name]))
        variables_names.append(variable[0])

    for constraints_var_n_value in constraints_var_n_values.items():
        rhs.append(constraints_var_n_value[1]["rhs"])


    return rhs, variables, lower_bounds, upper_bounds, variables_names, constraints_names, senses, constraints_var_n_values, types, obj


def parse_mps():
    rhs = []
    lower_bounds = []
    upper_bounds = []
    variables_names = []
    constraints_names = []
    types = ""
    senses = ""
    flag_read_parts = {"NAME": False,
                       "COLUMNS": False,
                       "ROWS": False,
                       "RHS": False,
                       "BOUNDS": False}

    constraints_var_n_values = {}
    rhs_values={}
    variables = {}
    obj_values = {}
    obj = []
    obj_name = ""

    marker_session = "C"
    for line in lines:
        if line.startswith("ROWS"):
            flag_read_parts["ROWS"] = True
            flag_read_parts["COLUMNS"] = False
            flag_read_parts["NAME"] = False
            flag_read_parts["RHS"] = False
            flag_read_parts["BOUNDS"] = False

        if line.startswith("COLUMNS"):
            flag_read_parts["ROWS"] = False
            flag_read_parts["COLUMNS"] = True
            flag_read_parts["NAME"] = False
            flag_read_parts["RHS"] = False
            flag_read_parts["BOUNDS"] = False

        if line.startswith("RHS"):
            flag_read_parts["ROWS"] = False
            flag_read_parts["COLUMNS"] = False
            flag_read_parts["NAME"] = False
            flag_read_parts["RHS"] = True
            flag_read_parts["BOUNDS"] = False

        if line.startswith("BOUNDS"):
            flag_read_parts["ROWS"] = False
            flag_read_parts["COLUMNS"] = False
            flag_read_parts["NAME"] = False
            flag_read_parts["RHS"] = False
            flag_read_parts["BOUNDS"] = True


        if flag_read_parts["ROWS"] and not line.startswith("ROWS"):
            if line.split()[0] != "N":
                senses = senses + (line.split()[0])
                name_constraint = line.split()[1]
                constraints_var_n_values[name_constraint] = {"variables": [],
                                                             "values": [],
                                                             "rhs": 0.00,

                                                             }
                constraints_names.append(name_constraint)
            elif line.split()[0] == "N":
                obj_name = line.split()[1]



        if flag_read_parts["COLUMNS"] and not line.startswith("COLUMNS"):

            fields = line.split()
            len(fields)

            if fields[0] not in variables and fields[0] != "MARK0000" and fields[0] != "MARK0001":
                variables[fields[0]] = {"constraint_names": [],
                                        "constraint_values": [],
                                        "LB": 0.00,
                                        "UB": cplex.infinity,
                                        "type": "C"}
            for index, field in enumerate(fields):
                if index!= 0:
                    if index%2 != 0 and field != "'MARKER'":
                        if field in constraints_var_n_values:
                            constraints_var_n_values[field]["variables"].append(fields[0])
                            constraints_var_n_values[field]["values"].append(float(fields[index+1]))
                            variables[fields[0]]["constraint_names"].append(fields[index])
                            variables[fields[0]]["constraint_values"].append(float(fields[index+1]))

                    if index%2 != 0 and field == obj_name:
                        obj_values[fields[0]] = fields[index+1]


            if fields[0] == "MARK0000":
                    marker_session = "I"

            elif fields[0] == "MARK00000":
                    marker_session = "C"

            if marker_session == "C" and fields[1] != "'MARKER'":
                variables[fields[0]].update( {"LB": float(0.00),
                                        "UB": cplex.infinity,
                                        "type": "C"})

            elif marker_session == "I" and fields[1] != "'MARKER'":
                variables[fields[0]].update({"LB": float(0.00),
                                        "UB": cplex.infinity,
                                        "type": "I"
                                       })


        if flag_read_parts["RHS"] and not line.startswith("RHS"):
            fields = line.split()

            for index, field in enumerate(fields):
                if index!=0:
                    if index%2 != 0:
                        constraints_var_n_values[field].update({"rhs": float(fields[index+1])})


        if flag_read_parts["BOUNDS"] and not line.startswith("BOUNDS"):
            fields = line.split()
            if fields[0] == "LO":
                variables[fields[2]].update({"LB": float(fields[3])})

            if fields[0] == "UP":
                variables[fields[2]].update({"UB": float(fields[3])})

            if fields[0] == "FX":
                variables[fields[2]].update({"LB": float(fields[3]),
                                             "UB": float(fields[3])})

            if fields[0] == "FR":
                variables[fields[2]].update({"LB": -cplex.infinity,
                                        "UB": cplex.infinity})

            if fields[0] == "MI":
                variables[fields[2]].update({"LB": -cplex.infinity})

            if fields[0] == "PL":
                variables[fields[2]].update({"LB": cplex.infinity})

            if fields[0] == "BV":
                print("")

            if fields[0] == "LI":
                variables[fields[2]].update({"LB": float(fields[3])})


            if fields[0] == "UI":
                variables[fields[2]].update({"UB": float(fields[3])})


            if fields[0] == "SC":
                variables[fields[2]].update({"LB": float(fields[3])})


            if fields[0] == "SI":
                variables[fields[2]].update({"UB": float(fields[3])})




    with open("constraints.json", "w") as outfile:
       json.dump(constraints_var_n_values, outfile, indent=4)

    with open("variables.json", "w") as outfile:
       json.dump(variables, outfile, indent=4)

    with open("objs.json", "w") as outfile:
       json.dump(obj_values, outfile, indent=4)


    for variable in variables.items():
        lower_bounds.append(variable[1]["LB"])
        upper_bounds.append(variable[1]["UB"])
        types = types + variable[1]["type"]
        if variable[0] in obj_values:
            obj.append(float(obj_values[variable[0]]))
        else:
            obj.append(0.0)
        variables_names.append(variable[0])

    for constraints_var_n_value in constraints_var_n_values.items():
        rhs.append(constraints_var_n_value[1]["rhs"])

    print(senses)
    print(types)

    return rhs, variables, lower_bounds, upper_bounds, variables_names, constraints_names, senses, constraints_var_n_values, types, obj


def populate_by_row(prob):
    rows = []
    rhs, variables, lower_bounds, upper_bounds, variables_names, constraints_names, senses, constraints_var_n_values, types, obj = parse_mps()
    for constraint in constraints_var_n_values.items():
        rows.append([constraint[1]["variables"], constraint[1]["values"]])

    prob.variables.add(obj = obj, lb = lower_bounds, ub=upper_bounds,
                       types = types, names=variables_names)
    print("rows" + str(rows))
    print("my obj vector" + str(obj))
    print("lower_bounds" + str(lower_bounds))
    print("upper_bounds" + str(upper_bounds))
    print("types" + str(types))
    print("name_variables" + str(variables_names))

    prob.linear_constraints.add(lin_expr=rows, senses=senses,
                                rhs=rhs, names=constraints_names)

    print("senses" + str(senses))
    print("rhs" + str(rhs))
    print("constraints_names" + str(constraints_names))



def populate_by_col(prob):
    columns = []
    rhs, variables, lower_bounds, upper_bounds, variables_names, constraints_names, senses, constraints_var_n_values, types, obj = parse_mps()
    prob.linear_constraints.add(senses=senses,
                                rhs=rhs, names=constraints_names)

    for variable in variables.items():
        columns.append([variable[1]["constraint_names"], variable[1]["constraint_values"]] )

    prob.variables.add(obj=obj, lb=lower_bounds, ub=upper_bounds,
                       names=variables_names, types=types, columns=columns)


def populate_by_non_zero(prob):
    aux = []
    vars_values_aux = []
    vals = []
    rows = []
    cols = []

    rhs, variables, lower_bounds, upper_bounds, variables_names, constraints_names, senses, constraints_var_n_values, types, obj = parse_mps()
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


    prob.linear_constraints.add(senses=senses,rhs=rhs, names=constraints_names)

    prob.variables.add(obj=obj, lb=lower_bounds, ub=upper_bounds, names=variables_names, types=types)


    prob.linear_constraints.set_coefficients(zip(rows, cols, vals))


def mipex1(pop_method):

    try:
        my_prob = cplex.Cplex()

        if pop_method == "r":
            print("Populate by row")
            populate_by_row(my_prob)

        elif pop_method == "c":
            print("Populate by col")
            populate_by_col(my_prob)

        elif pop_method == "n":
            print("Populate by non zero")
            populate_by_non_zero(my_prob)

        else:
            raise ValueError('pop_method must be one of "r", "c" or "n"')

        my_prob.solve()
    except CplexError as exc:
        print(exc)
        return

    print()
    print("Solution status = ", my_prob.solution.get_status(), ":", end=' ')
    print(my_prob.solution.status[my_prob.solution.get_status()])
    print("Solution value  = ", my_prob.solution.get_objective_value())

    numcols = my_prob.variables.get_num()
    numrows = my_prob.linear_constraints.get_num()

    slack = my_prob.solution.get_linear_slacks()
    x = my_prob.solution.get_values()
    #
    for j in range(numrows):
        print("Row %d:  Slack = %10f" % (j, slack[j]))
    for j in range(numcols):
        print("Column %d:  Value = %10f" % (j, x[j]))

    print("Solution value  = ", my_prob.solution.get_objective_value())



if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["-r", "-c", "-n"]:
        print("Usage: mipex1.py -X")
        print("   where X is one of the following options:")
        print("      r          generate problem by row")
        print("      c          generate problem by column")
        print("      n          generate problem by nonzero")
        print(" Exiting...")
        sys.exit(-1)
    mipex1(sys.argv[1][1])