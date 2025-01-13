import os
from itertools import product

def expand_pla_patterns(pattern):
    if '_' not in pattern:
        return [pattern]
    else:
        return expand_pla_patterns(pattern.replace('_', '0', 1)) + expand_pla_patterns(pattern.replace('_', '1', 1))

def read_pla_file(file_path):
    with open(file_path, 'r') as file:
        lines = [line.strip() for line in file if not line.startswith('#') and line.strip()]
    pla_pairs = [(line.split()[0], line.split()[1]) for line in lines if not line.startswith(('.i', '.o', '.p'))]
    expanded_pairs = []
    for inp, outp in pla_pairs:
        expanded_inputs = expand_pla_patterns(inp)
        for exp_inp in expanded_inputs:
            expanded_pairs.append((exp_inp, outp))
    return expanded_pairs

def print_pla_contents(pla_data, label):
    print(f"\nContents of {label}:")
    for i, (input_pattern, output_pattern) in enumerate(pla_data, start=1):
        print(f"{i}) {input_pattern} {output_pattern}")

def categorize_function_inputs(pla_data, active_state='1'):
    num_outputs = max(len(characteristic) for _, characteristic in pla_data)
    function_inputs = {f"f{i + 1}": set() for i in range(num_outputs)}
    for conjunction, characteristic in pla_data:
        for i, output in enumerate(characteristic):
            if output == active_state:
                function_inputs[f"f{i + 1}"].add(conjunction)
    return function_inputs

def print_function_inputs(function_inputs, label):
    print(f"\nInputs for functions from {label}:")
    for function, inputs in function_inputs.items():
        print(f"{function}: {', '.join(inputs)}")

def matches_pattern(bbtas_input, pattern):
    return all(pc == '-' or pc == bc for pc, bc in zip(pattern, bbtas_input))

def matches_pattern1(bbtas_input, pattern):
    intersection = []
    assert len(bbtas_input) == len(pattern), "Inputs and patterns must be of the same length."
    for pc, bc in zip(pattern, bbtas_input):
        if pc == '-':
            intersection.append(bc)
        elif bc == '-' and pc in '01':
            intersection.append(pc)
        elif pc == bc:
            intersection.append(pc)
        else:
            return None
    return ''.join(intersection) if intersection else None

def find_matching_inputs(truth_inputs, bbtas_data):
    max_length = max(len(input) for inputs in truth_inputs.values() for input in inputs)
    final_unique_intersections = {function: set() for function in truth_inputs.keys()}
    min_counts = {function: (float('inf'), None) for function in truth_inputs.keys()}
    bbtas_function_inputs = categorize_function_inputs(bbtas_data, active_state='0')
    for element in range(max_length):
        print(f"\nRemoving Element {element + 1}:")
        unique_intersections = {function: set() for function in truth_inputs.keys()}
        for function, inputs in truth_inputs.items():
            print(f"\nFor {function}:")
            for truth_input in inputs:
                if truth_input[element] != '-':
                    wildcard_input = truth_input[:element] + '-' + truth_input[element + 1:]
                    print(f"Checking conjunction: {wildcard_input}")
                    matched_inputs = [bbtas_input for bbtas_input in bbtas_function_inputs[function] if matches_pattern(bbtas_input, wildcard_input)]
                    if matched_inputs:
                        for match in matched_inputs:
                            print(f"Intersection: {match}")
                        unique_intersections[function].update(matched_inputs)
                    else:
                        print("Empty")
            count = len(unique_intersections[function])
            print(f"Count: {count}")
            if count > 0 and count < min_counts[function][0]:
                min_counts[function] = (count, element + 1)
        for function, intersections in unique_intersections.items():
            final_unique_intersections[function].update(intersections)
    print("\nTotal Count of Unique Intersections for each Function:")
    for function, intersections in final_unique_intersections.items():
        total_count = len(intersections)
        print(f"{function}: {total_count}")
    print("\nMinimum Count of Intersections for each Function (excluding 0):")
    for function, (min_count, step) in min_counts.items():
        if min_count < float('inf'):
            print(f"{function}: Min Count = {min_count} when REMOVING ELEMENT {step}")
    print("\nList of Unique Intersections for Each Function:")
    for function, intersections in final_unique_intersections.items():
        print(f"{function}: {', '.join(intersections)}")

def find_best_element_and_print(truth_inputs, bbtas_data):
    max_length = max(len(input) for inputs in truth_inputs.values() for input in inputs)
    final_unique_intersections = {function: set() for function in truth_inputs.keys()}
    bbtas_function_inputs = categorize_function_inputs(bbtas_data, active_state='0')
    best_intersections_for_functions = {}
    for function, inputs in truth_inputs.items():
        print(f"\nProcessing for {function}...")
        best_element_for_conjunctions = {}
        for truth_input in inputs:
            best_element = None
            smallest_count = float('inf')
            best_intersections_list = None
            for element in range(max_length):
                if truth_input[element] != '-':
                    wildcard_input = truth_input[:element] + '-' + truth_input[element + 1:]
                    matched_inputs = [bbtas_input for bbtas_input in bbtas_function_inputs[function] if matches_pattern(bbtas_input, wildcard_input)]
                    if matched_inputs:
                        count = len(matched_inputs)
                        if count < smallest_count:
                            smallest_count = count
                            best_element = element + 1
                            best_intersections_list = matched_inputs
            best_element_for_conjunctions[truth_input] = (best_element, best_intersections_list)
            if best_intersections_list is not None:
                final_unique_intersections[function].update(best_intersections_list)
        best_intersections_for_functions[function] = best_element_for_conjunctions
    print("\nBest Element and Intersections for Each Function:")
    for function, conjunctions in best_intersections_for_functions.items():
        print(f"\nFor {function}:")
        sorted_conjunctions = sorted(
            conjunctions.items(), 
            key=lambda x: (len(x[1][1]) if x[1][1] is not None else float('inf'), x[0])
        )
        for conjunction, (best_element, best_intersections_list) in sorted_conjunctions:
            if best_element is not None and best_intersections_list is not None:
                sorted_intersections = sorted(best_intersections_list)
                print(f"Conjunction: {conjunction}, Best Element: {best_element}, Intersections: {', '.join(sorted_intersections)}")
            else:
                print(f"Conjunction: {conjunction}, No valid best element found.")
    return best_intersections_for_functions

def generate_new_conjunctions_and_characteristics(best_intersections_for_functions, truth_pla): 
    print("\nGenerating New Conjunctions and Characteristics:") 
    assigned_characteristics = [] 
    for function, conjunctions in best_intersections_for_functions.items(): 
        function_idx = int(function[1:]) - 1  
         
        selected_conjunction = None 
        min_intersections = float('inf') 
        selected_best_element = None 
 
        for conjunction, (best_element, intersections) in conjunctions.items(): 
            if best_element is not None and intersections is not None: 
                intersection_count = len(intersections) 
                if 0 < intersection_count < min_intersections: 
                    min_intersections = intersection_count 
                    selected_conjunction = conjunction 
                    selected_best_element = best_element 
 
        print(f"\nFor {function}:") 
 
        for conjunction, (best_element, intersections) in conjunctions.items(): 
            if best_element is not None and intersections is not None: 
                intersection_count = len(intersections) 
                highlight = (conjunction == selected_conjunction) 
                print(f"Conjunction: {conjunction} (Intersections: {intersection_count})",  
                      " <-- Selected" if highlight else "") 
 
                original_characteristic = None 
                for truth_conjunction, characteristic in truth_pla: 
                    if truth_conjunction == conjunction: 
                        original_characteristic = characteristic 
                        break 
 
                if original_characteristic is None: 
                    print(f"  Conjunction: {conjunction} not found in truth.pla") 
                    continue 
 
                if highlight: 
                    new_characteristic_1 = list(original_characteristic) 
                    print(f"  Original Conjunction: {conjunction} -> New Conjunction: {conjunction}, Characteristic: {''.join(new_characteristic_1)}") 
 
                    new_characteristic_2 = ['0'] * len(original_characteristic) 
                    new_characteristic_2[function_idx] = '1'  
                    modified_conjunction = list(conjunction) 
                    modified_conjunction[best_element - 1] = '-'  
 
                    print(f"  Modified Conjunction: {''.join(modified_conjunction)}, Characteristic: {''.join(new_characteristic_2)}") 
 
                    assigned_characteristics.append((conjunction, ''.join(new_characteristic_1), "New Conjunction")) 
                    assigned_characteristics.append((''.join(modified_conjunction), ''.join(new_characteristic_2), "Modified Conjunction")) 
    return assigned_characteristics  

def generate_unique_characteristics_from_first_set(best_intersections_for_functions, truth_pla):
    print("\nGenerating Unique Characteristics from characteristic_1 for Each Function:")
    used_conjunctions = set()
    used_characteristics = set()
    assigned_characteristics = []
    for function, conjunctions in best_intersections_for_functions.items():
        function_idx = int(function[1:]) - 1
        print(f"\nFor {function}:")
        for conjunction, (best_element, best_intersections_list) in conjunctions.items():
            if conjunction in used_conjunctions:
                continue
            if best_element is not None and best_intersections_list is not None and len(best_intersections_list) == 1:
                original_characteristic = None
                for truth_conjunction, characteristic in truth_pla:
                    if truth_conjunction == conjunction:
                        original_characteristic = characteristic
                        break
                if original_characteristic is None:
                    print(f"Conjunction: {conjunction} not found in BSDNF")
                    continue
                characteristic_1 = list(original_characteristic)
                characteristic_1[function_idx] = '0'
                characteristic_str_1 = ''.join(characteristic_1)
                if characteristic_str_1 not in used_characteristics:
                    used_characteristics.add(characteristic_str_1)
                    used_conjunctions.add(conjunction)
                    assigned_characteristics.append((conjunction, characteristic_str_1, "New Conjunction", function))
                    print(f"New Conjunction and Characteristic Assigned:")
                    print(f"  Conjunction: {conjunction}, Characteristic: {characteristic_str_1}")
                    modified_conjunction = list(conjunction)
                    modified_conjunction[best_element - 1] = '-'
                    modified_conjunction_str = ''.join(modified_conjunction)
                    characteristic_2 = ['0'] * len(original_characteristic)
                    characteristic_2[function_idx] = '1'
                    characteristic_str_2 = ''.join(characteristic_2)
                    assigned_characteristics.append((modified_conjunction_str, characteristic_str_2, "Modified Conjunction", function))
                    print(f"Modified Conjunction and Characteristic Assigned:")
                    print(f"  Conjunction: {modified_conjunction_str}, Characteristic: {characteristic_str_2}")
                    break
                else:
                    print(f"[Info] Skipping characteristic: {characteristic_str_1} (already used)")

    print("\n--- All Assigned Unique Characteristics ---")
    for conjunction, characteristic, conj_type, function in assigned_characteristics:
        print(f"{conj_type}:")
        print(f"  Conjunction: {conjunction}, Assigned Characteristic: {characteristic}, Function: {function}\n")

    return assigned_characteristics


def generate_new_dnfs_list(assigned_characteristics, truth_data):
    print("\nРасщепляемые пары:")
    split_pairs = []
    row_index = 1

    dnf_list = []
    function_conjunctions = {}

    for i in range(0, len(assigned_characteristics), 2):
        new_conjunction, new_characteristic, _, function = assigned_characteristics[i]
        modified_conjunction, modified_characteristic, _, _ = assigned_characteristics[i + 1]
        split_pairs.append((new_conjunction, new_characteristic, modified_conjunction, modified_characteristic, function))

        print(f"{row_index}) {new_conjunction} {new_characteristic}")
        print(f"   {modified_conjunction} {modified_characteristic}")

        dnf_list.append((new_conjunction, new_characteristic))
        dnf_list.append((modified_conjunction, modified_characteristic))

        if function not in function_conjunctions:
            function_conjunctions[function] = []
        function_conjunctions[function].append(new_conjunction)
        function_conjunctions[function].append(modified_conjunction)

        row_index += 1

    print_pla_contents(truth_data, 'БФДНФ')

    print("\nDNFs List based on БФДНФ:")
    original_conjunctions = set()
    row_index = 1

    for conjunction, original_characteristic in truth_data:
        modified_found = False
        for new_conjunction, new_characteristic, modified_conjunction, modified_characteristic, _ in split_pairs:
            if conjunction == new_conjunction:
                print(f"{row_index}) {new_conjunction} {new_characteristic}")
                original_conjunctions.add(new_conjunction)
                print(f"   {modified_conjunction} {modified_characteristic}")
                modified_found = True
                dnf_list.append((new_conjunction, new_characteristic))
                dnf_list.append((modified_conjunction, modified_characteristic))
                break
        
        if not modified_found:
            print(f"{row_index}) {conjunction} {original_characteristic}")
            original_conjunctions.add(conjunction)
            dnf_list.append((conjunction, original_characteristic))
        row_index += 1

    function_inputs = categorize_function_inputs(dnf_list)
    print_function_inputs(function_inputs, "Function Inputs from DNF List")

    return split_pairs, dnf_list, original_conjunctions, function_conjunctions

def extract_and_print_intersections(best_intersections_for_functions, selected_conjunctions_with_functions):
    print("\nМножество наборов незащищенной области:")
    index = 1
    all_intersections = []
    for conjunction, function in selected_conjunctions_with_functions:
        if function in best_intersections_for_functions:
            conjunctions = best_intersections_for_functions[function]
            if conjunction in conjunctions:
                best_element, intersections = conjunctions[conjunction]
                if intersections is not None:
                    sorted_intersections = sorted(intersections)
                    intersection_str = ', '.join(sorted_intersections)
                    print(f"{index}) Conjunction: {conjunction} , Intersection: {intersection_str}")
                    index += 1
                    all_intersections.extend(intersections)
                else:
                    print(f"{index}) Conjunction: {conjunction} , No valid intersections found.")
                    index += 1
            else:
                print(f"{index}) Conjunction: {conjunction} not found in {function}")
                index += 1
        else:
            print(f"{index}) Function {function} not found")
            index += 1
    print()
    return all_intersections

def find_intersections_for_function(function_inputs, split_pairs):
    for function, inputs in function_inputs.items():
        print(f"\nChecking intersections for {function}:")
        for conjunction in inputs:
            print(f"  Checking conjunction: {conjunction}")
            corresponding_conjunctions = [pair[0] for pair in split_pairs if pair[0] != conjunction]
            print(f"    Corresponding conjunctions from split pairs: {corresponding_conjunctions}")
            no_intersections = 0
            for gen_conjunction in corresponding_conjunctions:
                intersection_found = False
                for input_conjunction in inputs:
                    intersection = matches_pattern1(input_conjunction, gen_conjunction)
                    if intersection:
                        intersection_found = True
                        break
                if not intersection_found:
                    no_intersections += 1
    return

def generate_binary_combinations(conjunction):
    wildcard_indices = [i for i, char in enumerate(conjunction) if char == '-']
    combinations = product('01', repeat=len(wildcard_indices))
    binary_combinations = []
    for combination in combinations:
        conjunction_list = list(conjunction)
        for idx, replacement in zip(wildcard_indices, combination):
            conjunction_list[idx] = replacement
        binary_combinations.append(''.join(conjunction_list))
    return binary_combinations

def intersection_match(conjunction_1, conjunction_2):
    if len(conjunction_1) != len(conjunction_2):
        return False
    for c1, c2 in zip(conjunction_1, conjunction_2):
        if c1 != '-' and c2 != '-' and c1 != c2:
            return False
    return True

def check_intersections(function_inputs):
    all_non_intersection_binaries = []
    for function, inputs in function_inputs.items():
        print(f"\nChecking intersections for {function}:")
        binary_conjunctions = {conjunction: generate_binary_combinations(conjunction) for conjunction in inputs}
        smallest_non_intersection_count = float('inf')
        smallest_non_intersection_conjunction = None
        smallest_non_intersection_binaries = []
        for conjunction, bin_combinations in binary_conjunctions.items():
            print(f"\n Checking conjunction: {conjunction}")
            print(f"    Binary combinations: {', '.join(bin_combinations)}")
            total_non_intersection_binaries = []
            for compare_conjunction, compare_bin_combinations in binary_conjunctions.items():
                if conjunction == compare_conjunction:
                    continue
                non_intersection_count = 0
                non_intersection_binaries = []
                skip_comparison = False
                for bin_1 in bin_combinations:
                    match_found = False
                    for bin_2 in compare_bin_combinations:
                        if intersection_match(bin_1, bin_2):
                            skip_comparison = True
                            break
                    if skip_comparison:
                        break
                    if not match_found:
                        non_intersection_count += 1
                        non_intersection_binaries.append(bin_1)
                if skip_comparison:
                    break
                total_non_intersection_binaries.extend(non_intersection_binaries)
                non_intersection_count = len(total_non_intersection_binaries)
                if 0 < non_intersection_count < smallest_non_intersection_count:
                    smallest_non_intersection_count = non_intersection_count
                    smallest_non_intersection_conjunction = conjunction
                    smallest_non_intersection_binaries = non_intersection_binaries
        if smallest_non_intersection_conjunction:
            print(f"\nSmallest non-intersection count for {function}: {smallest_non_intersection_count} (Conjunction: {smallest_non_intersection_conjunction})")
            print(f"Binary combinations that did not match: {', '.join(smallest_non_intersection_binaries)}")
            all_non_intersection_binaries.extend(smallest_non_intersection_binaries)
        else:
            print(f"\nNo non-intersection counts greater than 0 found for {function}.")
    unique_non_intersection_binaries = sorted(set(all_non_intersection_binaries))
    if all_non_intersection_binaries:
        num_variables = len(unique_non_intersection_binaries[0])
        total_combinations = 2 ** num_variables
        percentage = (len(unique_non_intersection_binaries)/ total_combinations) * 100
        print("\nAll binary combinations that did not match for all functions:")
        print('\n'.join(all_non_intersection_binaries))
        print(f"\nTotal number of unique non-intersecting binaries: {len(unique_non_intersection_binaries)}")
        print(f"Total possible combination (2^{num_variables}): {total_combinations}")
        print(f"Percentage = {percentage}")
    else:
        print("\nNo non-intersecting binaries found across all functions.")

def main():
    print("Current Working Directory:", os.getcwd())
    print("Files in Directory:", os.listdir(os.getcwd()))

    truth_file_path = 'sand_k2k_min.pla'  
    bbtas_file_path = 'sand_k2k_fr.pla'  

    if not all(os.path.exists(file_path) for file_path in [truth_file_path, bbtas_file_path]):
        print("One or more files are missing.")
        return

    truth_data = read_pla_file(truth_file_path)
    bbtas_data = read_pla_file(bbtas_file_path)

    print_pla_contents(truth_data, 'truth1.pla')
    print_pla_contents(bbtas_data, 'bbtas_k2k_fr.pla')

    truth_function_inputs = categorize_function_inputs(truth_data, active_state='1')
    print_function_inputs(truth_function_inputs, 'БСДНФ (f=1)')

    bbtas_function_inputs = categorize_function_inputs(bbtas_data, active_state='0')
    print_function_inputs(bbtas_function_inputs, 'частичной функции (f=0)')

    find_matching_inputs(truth_function_inputs, bbtas_data)

    best_intersections_for_functions = find_best_element_and_print(truth_function_inputs, bbtas_data)

    assigned_characteristics = generate_new_conjunctions_and_characteristics(best_intersections_for_functions, truth_data)

    unique_characteristics_table = generate_unique_characteristics_from_first_set(best_intersections_for_functions, truth_data)

    split_pairs, dnf_list, original_conjunctions, function_conjunctions = generate_new_dnfs_list(unique_characteristics_table, truth_data)

    desired_conjunctions_with_functions = []
    for new_conjunction, _, _, _, function in split_pairs:
        desired_conjunctions_with_functions.append((new_conjunction, function))

    all_intersections = extract_and_print_intersections(best_intersections_for_functions, desired_conjunctions_with_functions)

    function_inputs = categorize_function_inputs(dnf_list)
    check_intersections(function_inputs)

    unique_intersections = sorted(set(all_intersections))
    num_variables = len(unique_intersections[0])
    total_combinations = 2 ** num_variables
    percentage = (len(unique_intersections)/ total_combinations) * 100

    print(f"\nTotal number of unique non-intersecting binaries: {len(unique_intersections)}")
    print(f"Total possible combination (2^{num_variables}): {total_combinations}")
    print(f"Percentage = {percentage}")
    print("Множество наборов незащищенной области (не совпадают):")
    for index, intersection in enumerate(unique_intersections, start=1):
        print(f"{index}) {intersection}")

if __name__ == '__main__':
    main()

