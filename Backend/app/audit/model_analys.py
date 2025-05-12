import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import subprocess
import shutil
import csv
import pandas as pd
import numpy as np
import re
import joblib

load_dotenv()

ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
OUTPUT_DIR = Path('./extracted-contracts')

target_columns_ordered = [
    "duration", "errors", "fails", "conkas_findings_amount", 
    "slither-0.10.4_findings_amount", "smartcheck_findings_amount", 
    "solhint-3.3.8_findings_amount", "total_findings_amount", 
    "conkas_vuln_Integer_Overflow", "conkas_vuln_Integer_Underflow", 
    "conkas_vuln_Reentrancy", "conkas_vuln_Time_Manipulation", 
    "conkas_vuln_Transaction_Ordering_Dependence", "conkas_vuln_Unchecked_Low_Level_Call", 
    "slither-0.10.4_vuln_arbitrary_send_erc20", "slither-0.10.4_vuln_arbitrary_send_eth", 
    "slither-0.10.4_vuln_assembly", "slither-0.10.4_vuln_assert_state_change", 
    "slither-0.10.4_vuln_boolean_cst", "slither-0.10.4_vuln_boolean_equal", 
    "slither-0.10.4_vuln_cache_array_length", "slither-0.10.4_vuln_calls_loop", 
    "slither-0.10.4_vuln_constable_states", "slither-0.10.4_vuln_constant_function_asm", 
    "slither-0.10.4_vuln_constant_function_state", "slither-0.10.4_vuln_controlled_array_length", 
    "slither-0.10.4_vuln_controlled_delegatecall", "slither-0.10.4_vuln_costly_loop", 
    "slither-0.10.4_vuln_cyclomatic_complexity", "slither-0.10.4_vuln_dead_code", 
    "slither-0.10.4_vuln_deprecated_standards", "slither-0.10.4_vuln_divide_before_multiply", 
    "slither-0.10.4_vuln_encode_packed_collision", "slither-0.10.4_vuln_erc20_indexed", 
    "slither-0.10.4_vuln_erc20_interface", "slither-0.10.4_vuln_erc721_interface", 
    "slither-0.10.4_vuln_events_access", "slither-0.10.4_vuln_events_maths", 
    "slither-0.10.4_vuln_external_function", "slither-0.10.4_vuln_function_init_state", 
    "slither-0.10.4_vuln_incorrect_equality", "slither-0.10.4_vuln_incorrect_exp", 
    "slither-0.10.4_vuln_incorrect_modifier", "slither-0.10.4_vuln_locked_ether", 
    "slither-0.10.4_vuln_low_level_calls", "slither-0.10.4_vuln_mapping_deletion", 
    "slither-0.10.4_vuln_missing_inheritance", "slither-0.10.4_vuln_missing_zero_check", 
    "slither-0.10.4_vuln_msg_value_loop", "slither-0.10.4_vuln_naming_convention", 
    "slither-0.10.4_vuln_pragma", "slither-0.10.4_vuln_public_mappings_nested", 
    "slither-0.10.4_vuln_redundant_statements", "slither-0.10.4_vuln_reentrancy_benign", 
    "slither-0.10.4_vuln_reentrancy_eth", "slither-0.10.4_vuln_reentrancy_events", 
    "slither-0.10.4_vuln_reentrancy_no_eth", "slither-0.10.4_vuln_reentrancy_unlimited_gas", 
    "slither-0.10.4_vuln_return_bomb", "slither-0.10.4_vuln_reused_constructor", 
    "slither-0.10.4_vuln_shadowing_abstract", "slither-0.10.4_vuln_shadowing_builtin", 
    "slither-0.10.4_vuln_shadowing_local", "slither-0.10.4_vuln_shadowing_state", 
    "slither-0.10.4_vuln_solc_version", "slither-0.10.4_vuln_suicidal", 
    "slither-0.10.4_vuln_tautological_compare", "slither-0.10.4_vuln_tautology", 
    "slither-0.10.4_vuln_timestamp", "slither-0.10.4_vuln_too_many_digits", 
    "slither-0.10.4_vuln_tx_origin", "slither-0.10.4_vuln_unchecked_lowlevel", 
    "slither-0.10.4_vuln_unchecked_send", "slither-0.10.4_vuln_unchecked_transfer", 
    "slither-0.10.4_vuln_unimplemented_functions", "slither-0.10.4_vuln_uninitialized_local", 
    "slither-0.10.4_vuln_uninitialized_state", "slither-0.10.4_vuln_uninitialized_storage", 
    "slither-0.10.4_vuln_unused_return", "slither-0.10.4_vuln_unused_state", 
    "slither-0.10.4_vuln_variable_scope", "slither-0.10.4_vuln_void_cst", 
    "slither-0.10.4_vuln_weak_prng", "slither-0.10.4_vuln_write_after_write", 
    "smartcheck_vuln_SOLIDITY_ADDRESS_HARDCODED", "smartcheck_vuln_SOLIDITY_ARRAY_LENGTH_MANIPULATION", 
    "smartcheck_vuln_SOLIDITY_BALANCE_EQUALITY", "smartcheck_vuln_SOLIDITY_BYTE_ARRAY_INSTEAD_BYTES", 
    "smartcheck_vuln_SOLIDITY_CALL_WITHOUT_DATA", "smartcheck_vuln_SOLIDITY_DEPRECATED_CONSTRUCTIONS", 
    "smartcheck_vuln_SOLIDITY_DIV_MUL", "smartcheck_vuln_SOLIDITY_ERC20_APPROVE", 
    "smartcheck_vuln_SOLIDITY_ERC20_FUNCTIONS_ALWAYS_RETURN_FALSE", "smartcheck_vuln_SOLIDITY_ERC20_TRANSFER_SHOULD_THROW", 
    "smartcheck_vuln_SOLIDITY_EXACT_TIME", "smartcheck_vuln_SOLIDITY_EXTRA_GAS_IN_LOOPS", 
    "smartcheck_vuln_SOLIDITY_FUNCTIONS_RETURNS_TYPE_AND_NO_RETURN", "smartcheck_vuln_SOLIDITY_GAS_LIMIT_IN_LOOPS", 
    "smartcheck_vuln_SOLIDITY_INCORRECT_BLOCKHASH", "smartcheck_vuln_SOLIDITY_LOCKED_MONEY", 
    "smartcheck_vuln_SOLIDITY_MSGVALUE_EQUALS_ZERO", "smartcheck_vuln_SOLIDITY_OVERPOWERED_ROLE", 
    "smartcheck_vuln_SOLIDITY_PRAGMAS_VERSION", "smartcheck_vuln_SOLIDITY_PRIVATE_MODIFIER_DONT_HIDE_DATA", 
    "smartcheck_vuln_SOLIDITY_REDUNDANT_FALLBACK_REJECT", "smartcheck_vuln_SOLIDITY_REVERT_REQUIRE", 
    "smartcheck_vuln_SOLIDITY_SAFEMATH", "smartcheck_vuln_SOLIDITY_SEND", 
    "smartcheck_vuln_SOLIDITY_SHOULD_NOT_BE_PURE", "smartcheck_vuln_SOLIDITY_SHOULD_NOT_BE_VIEW", 
    "smartcheck_vuln_SOLIDITY_SHOULD_RETURN_STRUCT", "smartcheck_vuln_SOLIDITY_TRANSFER_IN_LOOP", 
    "smartcheck_vuln_SOLIDITY_TX_ORIGIN", "smartcheck_vuln_SOLIDITY_UINT_CANT_BE_NEGATIVE", 
    "smartcheck_vuln_SOLIDITY_UNCHECKED_CALL", "smartcheck_vuln_SOLIDITY_UPGRADE_TO_050", 
    "smartcheck_vuln_SOLIDITY_USING_INLINE_ASSEMBLY", "smartcheck_vuln_SOLIDITY_VAR", 
    "smartcheck_vuln_SOLIDITY_VAR_IN_LOOP_FOR", "smartcheck_vuln_SOLIDITY_VISIBILITY", 
    "solhint-3.3.8_vuln_avoid_call_value", "solhint-3.3.8_vuln_avoid_low_level_calls", 
    "solhint-3.3.8_vuln_avoid_sha3", "solhint-3.3.8_vuln_avoid_suicide", 
    "solhint-3.3.8_vuln_avoid_throw", "solhint-3.3.8_vuln_avoid_tx_origin", 
    "solhint-3.3.8_vuln_check_send_result", "solhint-3.3.8_vuln_compiler_version", 
    "solhint-3.3.8_vuln_const_name_snakecase", "solhint-3.3.8_vuln_contract_name_camelcase", 
    "solhint-3.3.8_vuln_event_name_camelcase", "solhint-3.3.8_vuln_func_name_mixedcase", 
    "solhint-3.3.8_vuln_func_visibility", "solhint-3.3.8_vuln_max_states_count", 
    "solhint-3.3.8_vuln_multiple_sends", "solhint-3.3.8_vuln_no_complex_fallback", 
    "solhint-3.3.8_vuln_no_empty_blocks", "solhint-3.3.8_vuln_no_inline_assembly", 
    "solhint-3.3.8_vuln_no_unused_vars", "solhint-3.3.8_vuln_not_rely_on_block_hash", 
    "solhint-3.3.8_vuln_not_rely_on_time", "solhint-3.3.8_vuln_payable_fallback", 
    "solhint-3.3.8_vuln_quotes", "solhint-3.3.8_vuln_reason_string", 
    "solhint-3.3.8_vuln_reentrancy", "solhint-3.3.8_vuln_state_visibility", 
    "solhint-3.3.8_vuln_use_forbidden_name", "solhint-3.3.8_vuln_var_name_mixedcase", 
    "solhint-3.3.8_vuln_visibility_modifier_order"
]

model_files = [
    "Gradient_Boosting__Tuned.joblib",
    "voting_classifier_ensemble.joblib",
    "XGBoost.joblib",
    "LightGBM.joblib",
    "Random_Forest__Tuned.joblib"
]

columns_to_remove = [
                        'fails',
                        'solhint-3.3.8_vuln_avoid_low_level_calls',
                        'solhint-3.3.8_vuln_avoid_throw',
                        'solhint-3.3.8_vuln_no_inline_assembly',
                        'solhint-3.3.8_vuln_not_rely_on_time',
                        'smartcheck_vuln_SOLIDITY_BYTE_ARRAY_INSTEAD_BYTES_log',
                        'smartcheck_vuln_SOLIDITY_BYTE_ARRAY_INSTEAD_BYTES_cbrt',
                        'smartcheck_vuln_SOLIDITY_BYTE_ARRAY_INSTEAD_BYTES_sqrt',
                        'smartcheck_vuln_SOLIDITY_VAR_IN_LOOP_FOR_log',
                        'smartcheck_vuln_SOLIDITY_VAR_IN_LOOP_FOR_cbrt',
                        'smartcheck_vuln_SOLIDITY_VAR_IN_LOOP_FOR_sqrt',
                        'slither-0.10.4_vuln_incorrect_exp_log',
                        'slither-0.10.4_vuln_incorrect_exp_cbrt',
                        'slither-0.10.4_vuln_public_mappings_nested_log',
                        'slither-0.10.4_vuln_public_mappings_nested_cbrt',
                        'slither-0.10.4_vuln_encode_packed_collision_log',
                        'slither-0.10.4_vuln_encode_packed_collision_sqrt',
                        'slither-0.10.4_vuln_tautological_compare_log',
                        'slither-0.10.4_vuln_tautological_compare_sqrt'
                    ]

reparse_command = ["./app/audit/smartbugs/reparse", "results"]

models_dir = "./app/audit/trained_models"



def get_contract_source_code(contract_address: str, chain: str) -> dict | None:
    """
    Получает и сохраняет исходный код контракта с Etherscan-подобного API (Basescan).
    """
    if not ETHERSCAN_API_KEY:
        print("Ошибка: ETHERSCAN_API_KEY не найден в переменных окружения.")
        return None
    
    chains = {
        "base": "8453",
        "mainnet": "1",
        "arbitrum": "42161",
    }
    
    api_url = "https://api.etherscan.io/v2/api";
    params = {
      "chainid": chains[chain],
      "module": "contract",
      "action": "getsourcecode",
      "address": contract_address,
      "apikey": ETHERSCAN_API_KEY
    };

    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"HTTP ошибка! {e}")
        return None

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        print(f"Не удалось разобрать JSON ответ: {e}")
        return None

    if data.get('status') == '1' and data.get('result') and len(data['result']) > 0:
        source_code_wrapper_str = data['result'][0].get('SourceCode')
        contract_name = data['result'][0].get('ContractName')

        if not source_code_wrapper_str:
            print("Поле 'SourceCode' пустое или отсутствует в ответе API.")
            return None

        if len(source_code_wrapper_str) < 2:
            print(f"Строка 'SourceCode' слишком короткая для применения логики substring: '{source_code_wrapper_str}'")
            return None
        
        string_to_parse_as_json = source_code_wrapper_str[1:-1]
        
        try:
            parsed_sources_object = json.loads(string_to_parse_as_json)
        except json.JSONDecodeError as e:
            print(f"Не удалось разобрать обработанную строку SourceCode JSON: {e}")
            return None

        if 'sources' not in parsed_sources_object:
            print("Разобранный JSON объект не содержит ключ 'sources'.")
            return None

        sources = parsed_sources_object['sources']
        
        
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for file_path_str in sources.keys():
            if contract_name in file_path_str:
                main_file_path = OUTPUT_DIR / Path(file_path_str)
                main_file_path.parent.mkdir(parents=True, exist_ok=True)
                main_file_path.write_text(sources[file_path_str]['content'], encoding='utf-8')
        
        print(f"Извлечение исходных кодов контракта в '{OUTPUT_DIR.resolve()}'...")
        for file_path_str, source_data in sources.items():
            if 'content' not in source_data:
                print(f"Предупреждение: ключ 'content' отсутствует для исходного файла '{file_path_str}'. Пропускаем.")
                continue
            
            content = source_data['content']
            full_file_path = OUTPUT_DIR / Path(file_path_str)
            full_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                full_file_path.write_text(content, encoding='utf-8')
                print(f"Файл сохранен: {full_file_path}")
            except IOError as e:
                print(f"Ошибка записи файла {full_file_path}: {e}")
        
        print(f"Все файлы сохранены в директории: {OUTPUT_DIR.resolve()}")
        print(f"Основной файл: {main_file_path}")
        return main_file_path

    else:
        error_message = data.get('message', 'Неизвестная ошибка')
        if data.get('result'):
             error_message += f" (Результат: {data.get('result')})"
        print(f"Ошибка получения исходного кода контракта: {error_message}")
        return None

def get_analysis_files(main_file_path, chain, contract_address):
    if main_file_path:
        try:
            # main_file_path является объектом Path (или None), преобразуем в строку для команды
            file_to_analyze_str = str(main_file_path)

            smartbugs_command = [
                "./app/audit/smartbugs/smartbugs",
                "-t", "fast",
                "-f", f"{file_to_analyze_str}",
                "--processes", "6",
                "--mem-limit", "2g",
                "--timeout", "30"
            ]
            
            chains_names = {
                "base": "base",
                "mainnet": "mainnet",
                "arbitrum": "arbi",
            }
            
            slither_command = [
                "slither",
                f"{chains_names[chain]}:{contract_address}",
                "--etherscan-apikey",
                f"{ETHERSCAN_API_KEY}",
                "--json",
                "-"
            ]

            # Запуск команды SmartBugs
            process = subprocess.run(smartbugs_command, capture_output=True, text=True, check=False)
            process_slither = subprocess.run(slither_command, capture_output=True, text=True, check=False)
            slither_analysis_data_for_csv = None # <--- Добавлено: инициализация переменной
            
            if process_slither.stdout and process_slither.stdout.strip():
                slither_output_data = json.loads(process_slither.stdout.strip())
                if slither_output_data.get("success") and slither_output_data.get("results") and slither_output_data["results"].get("detectors"):
                    slither_analysis_data = set([detector['check'] for detector in slither_output_data['results']['detectors']])
                    slither_analysis_data_for_csv = slither_analysis_data # <--- Добавлено: сохранение данных для CSV

                if process.returncode == 0: # Продолжаем, только если SmartBugs завершился успешно
                    try:
                        reparse_process = subprocess.run(reparse_command, capture_output=True, text=True, check=False)
                        if reparse_process.returncode == 0:
                            results2csv_command_str = "./app/audit/smartbugs/results2csv -p results > results.csv"
                            try:
                                results2csv_process = subprocess.run(results2csv_command_str, shell=True, capture_output=True, text=True, check=False)
                                if results2csv_process.returncode == 0:
                                    print("./results2csv успешно завершен. Файл results.csv должен быть создан.")

                                    results_dir_path = Path("./results")
                                    if results_dir_path.exists() and results_dir_path.is_dir():
                                        try:
                                            shutil.rmtree(results_dir_path)
                                        except OSError as e:
                                            print(f"Ошибка при удалении директории {results_dir_path}: {e}")
                                    else:
                                        print(f"\nДиректория {results_dir_path} не найдена или не является директорией. Пропуск удаления.")

                            except FileNotFoundError:
                                print("\nОшибка: Исполняемый файл './results2csv' не найден.")
                            except Exception as e:
                                print(f"\nПроизошла ошибка при запуске ./results2csv: {e}")
                    except FileNotFoundError:
                        print("\nОшибка: Исполняемый файл './reparse' не найден.")
                    except Exception as e:
                        print(f"\nПроизошла ошибка при запуске ./reparse: {e}")

                    # Добавление результатов анализа Slither в results.csv <--- Начало нового блока
                    if slither_analysis_data_for_csv is not None and main_file_path is not None:
                        results_csv_path = Path("./results.csv")
                        # Проверяем существует ли файл и не пустой ли он для определения необходимости записи заголовка
                        file_exists = results_csv_path.exists()
                        is_empty = True
                        if file_exists:
                            try:
                                if results_csv_path.stat().st_size > 0:
                                    is_empty = False
                            except OSError as e:
                                print(f"Не удалось проверить размер файла {results_csv_path}: {e}. Предполагаем, что он пуст или его нужно создать.")
                                file_exists = False # Если не можем прочитать размер, считаем что его нет для записи заголовка


                        slither_row_data = [
                            str(main_file_path),                                                             # filename
                            main_file_path.name,                                                             # basename
                            "slither-0.10.4",                                                                # toolId
                            "solidity",                                                                      # toolmode
                            "0.10.4",                                                                        # parser_version (извлечено из toolId)
                            "0",                                                                             # runid
                            "0",                                                                             # start
                            "0",                                                                             # duration
                            "0",                                                                             # exit_code
                            f"{{{','.join(sorted(list(slither_analysis_data_for_csv)))}}}",                  # infos
                            "{}",                                                                            # errors
                            "{}",                                                                            # fails
                            "{}",                                                                            # findings
                        ]
                        
                        csv_headers = ["filename", "basename", "toolId", "toolmode", "parser_version", "runid", "start", "duration", "exit_code", "infos", "errors", "fails", "findings"]

                        try:
                            with open(results_csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                                writer = csv.writer(csvfile)
                                if not file_exists or is_empty:
                                    writer.writerow(csv_headers)
                                writer.writerow(slither_row_data)
                        except IOError as e:
                            print(f"Ошибка записи данных Slither в {results_csv_path}: {e}")
                    elif main_file_path is None:
                        print("\nНе удалось добавить результаты Slither в CSV: main_file_path не определен.")
                    else:
                        print("\nНе удалось добавить результаты Slither в CSV: данные анализа отсутствуют.")
                else:
                    print("\nПропуск reparse, results2csv и удаления директории results из-за предыдущих ошибок SmartBugs.")

        except FileNotFoundError:
            print("\nОшибка: Исполняемый файл './smartbugs' не найден.")
            print("Убедитесь, что он находится в текущей рабочей директории (откуда запускается скрипт),")
            print("имеет права на выполнение, или укажите полный путь к нему.")
        except Exception as e:
            print(f"\nПроизошла ошибка при запуске SmartBugs: {e}")
    else:
        print("\nПуть к основному файлу контракта (main_file_path) не определен.")
        print("Анализ SmartBugs не будет запущен.")

def parse_findings(findings_str):
    """Parses a string like '{Vuln1,Vuln2}' into a set {'Vuln1', 'Vuln2'}."""
    if pd.isna(findings_str): return set()
    if isinstance(findings_str, str):
        if findings_str == '{}': return set()
        try:
            cleaned_str = findings_str.strip().strip('{}')
            if not cleaned_str: return set()
            vulns = {item.strip() for item in cleaned_str.split(',')}
            return {v for v in vulns if v}
        except Exception as e: return set()
    elif isinstance(findings_str, set): return findings_str
    else: return set()
    
def get_data_to_predict(df):
    processed_rows = []
    unique_vulns_by_tool = {}
    processed_tool_ids = set()
    if not df.empty and 'toolid' in df.columns and 'findings' in df.columns and 'basename' in df.columns:
        columns_to_exclude_initially = ['toolid', 'findings']
        if 'errors' in df.columns: columns_to_exclude_initially.append('errors')
        if 'fails' in df.columns: columns_to_exclude_initially.append('fails')

        columns_to_drop_later = ['filename', 'toolmode', 'parser_version', 'runid', 'start', 'exit_code', 'infos']

        existing_columns_to_drop = [col for col in columns_to_drop_later if col in df.columns]
        base_columns = df.columns.drop(columns_to_exclude_initially + existing_columns_to_drop, errors='ignore').tolist()

        if 'basename' in base_columns:
            base_columns.remove('basename')

        for basename, group in df.groupby('basename'):
            combined_row = {}
            first_row = group.iloc[0]
            for col in base_columns:
                if col in first_row.index: combined_row[col] = first_row[col]
                else: combined_row[col] = np.nan

            combined_row['basename'] = basename

            findings_sets_this_row = {}
            for index, row in group.iterrows():
                tool_name = row['toolid']
                processed_tool_ids.add(tool_name) # Add tool id to the set
                findings_str = row['findings']
                parsed_set = parse_findings(findings_str)
                findings_sets_this_row[tool_name] = parsed_set
                issue_col_name = f"{tool_name}_findings" # This column will store the SET
                combined_row[issue_col_name] = parsed_set

                if tool_name not in unique_vulns_by_tool: unique_vulns_by_tool[tool_name] = set()
                unique_vulns_by_tool[tool_name].update(parsed_set)

            # --- Fill missing tool findings with empty sets for consistent columns ---
            for tool_id in processed_tool_ids:
                issue_col_name = f"{tool_id}_findings"
                if issue_col_name not in combined_row:
                    combined_row[issue_col_name] = set() # Ensure column exists for all rows

            if 'errors' in df.columns: combined_row['errors'] = 1 if first_row.get('errors', '{}') != '{}' else 0
            if 'fails' in df.columns: combined_row['fails'] = 1 if first_row.get('fails', '{}') != '{}' else 0

            processed_rows.append(combined_row)

        df_intermediate = pd.DataFrame(processed_rows)

        amount_cols_list = []
        for tool_id in processed_tool_ids:
            findings_col = f"{tool_id}_findings"
            amount_col_name = f"{tool_id}_findings_amount"
            if findings_col in df_intermediate.columns:
                df_intermediate[amount_col_name] = df_intermediate[findings_col].apply(lambda x: len(x) if isinstance(x, set) else 0)
                amount_cols_list.append(amount_col_name)
            else:
                df_intermediate[amount_col_name] = 0
                amount_cols_list.append(amount_col_name)


        if amount_cols_list:
            df_intermediate['total_findings_amount'] = df_intermediate[amount_cols_list].sum(axis=1)
            print("  Столбец 'total_findings_amount' создан.")
        else:
            df_intermediate['total_findings_amount'] = 0
            print("  Столбец 'total_findings_amount' создан (значение 0).")


        columns_actually_present_to_drop = [col for col in columns_to_drop_later if col in df_intermediate.columns]
        if 'basename' in df_intermediate.columns: columns_actually_present_to_drop.append('basename')
        findings_set_cols_to_drop = [col for col in df_intermediate.columns if col.endswith('_findings')]

        df_final_base = df_intermediate.drop(columns=columns_actually_present_to_drop + findings_set_cols_to_drop, errors='ignore')


        new_binary_columns = {}
        for tool_id, unique_vulns in unique_vulns_by_tool.items():
            tool_findings_col = f"{tool_id}_findings"
            if tool_findings_col not in df_intermediate.columns:
                continue

            if not unique_vulns: continue

            for vuln in sorted(list(unique_vulns)):
                if not vuln: continue
                sanitized_vuln_name = re.sub(r'\W+', '_', vuln).strip('_')
                if not sanitized_vuln_name: sanitized_vuln_name = "unknown_vuln"
                new_col_name = f"{tool_id}_vuln_{sanitized_vuln_name}"
                new_binary_columns[new_col_name] = df_intermediate[tool_findings_col].apply(
                    lambda findings_set: 1 if isinstance(findings_set, set) and vuln in findings_set else 0
                )

        if new_binary_columns:
            df_binary_vulns = pd.DataFrame(new_binary_columns, index=df_final_base.index)
            df_final = pd.concat([df_final_base, df_binary_vulns], axis=1)
        else:
            df_final = df_final_base

        for col in target_columns_ordered:
            if col not in df_final.columns:
                df_final[col] = 0

        columns_to_select = [col for col in target_columns_ordered if col in df_final.columns]
        df_final = df_final[columns_to_select]
        
        extra_columns = [col for col in df_final.columns if col not in target_columns_ordered]
        if extra_columns:
            df_final = df_final.drop(columns=extra_columns, errors='ignore')
            

        df = df_final

        column_name = 'smartcheck_vuln_SOLIDITY_BYTE_ARRAY_INSTEAD_BYTES'
        df[f'{column_name}_log'] = np.log1p(df[column_name])
        df[f'{column_name}_cbrt'] = df[column_name].apply(lambda x: x**(1/3))
        df[f'{column_name}_sqrt'] = np.sqrt(df[column_name])

        column_name = 'smartcheck_vuln_SOLIDITY_VAR_IN_LOOP_FOR'
        df[f'{column_name}_log'] = np.log1p(df[column_name])
        df[f'{column_name}_cbrt'] = df[column_name].apply(lambda x: x**(1/3))
        df[f'{column_name}_sqrt'] = np.sqrt(df[column_name])
        
        df = df_final

        column_name = 'slither-0.10.4_vuln_incorrect_exp'
        df[f'{column_name}_log'] = np.log1p(df[column_name])
        df[f'{column_name}_cbrt'] = df[column_name].apply(lambda x: x**(1/3))

        column_name = 'slither-0.10.4_vuln_public_mappings_nested'
        df[f'{column_name}_log'] = np.log1p(df[column_name])
        df[f'{column_name}_cbrt'] = df[column_name].apply(lambda x: x**(1/3))
        
        df = df_final

        column_name = 'slither-0.10.4_vuln_encode_packed_collision'
        df[f'{column_name}_log'] = np.log1p(df[column_name])
        df[f'{column_name}_sqrt'] = np.sqrt(df[column_name])

        df = df_final

        column_name = 'slither-0.10.4_vuln_tautological_compare'
        df[f'{column_name}_log'] = np.log1p(df[column_name])
        df[f'{column_name}_sqrt'] = np.sqrt(df[column_name])

        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)

        return df_final

    else:
        print("Исходный DataFrame пуст или не содержит необходимых столбцов...")
        
def predict_data(df_final):
    print("\n--- Запуск предсказаний на основе обученных моделей ---")
    imputer_path = os.path.join(models_dir, "imputer.joblib")
    scaler_path = os.path.join(models_dir, "scaler.joblib")
    model_outputs = {} # Инициализация объекта для сбора результатов

    if 'df_final' not in locals() or df_final.empty:
        print("Ошибка: DataFrame 'df_final' не найден или пуст для предсказаний.")
        print("Пожалуйста, убедитесь, что предыдущие шаги анализа и обработки данных выполнены успешно.")
    else:
        print(f"DataFrame 'df_final' для предсказаний найден. Размер: {df_final.shape}")

        X_to_predict = df_final.copy()

        try:
            if not os.path.exists(imputer_path):
                print(f"Ошибка: Файл импьютера не найден по пути: {imputer_path}")
                raise FileNotFoundError(f"Imputer not found: {imputer_path}")
            if not os.path.exists(scaler_path):
                print(f"Ошибка: Файл скейлера не найден по пути: {scaler_path}")
                raise FileNotFoundError(f"Scaler not found: {scaler_path}")

            imputer = joblib.load(imputer_path)
            scaler = joblib.load(scaler_path)

            X_imputed = imputer.transform(X_to_predict)
            
            _X_scaled_before_drop = scaler.transform(X_imputed)

            _df_scaled_before_drop = pd.DataFrame(_X_scaled_before_drop, columns=X_to_predict.columns)
            
            _df_scaled_after_drop = _df_scaled_before_drop.drop(columns=columns_to_remove, errors='ignore')
            
            X_scaled = _df_scaled_after_drop.values

            for model_file_name in model_files:
                model_path = os.path.join(models_dir, model_file_name)
                if not os.path.exists(model_path):
                    print(f"Предупреждение: Файл модели не найден по пути: {model_path}. Пропуск этой модели.")
                    continue
                try:
                    model = joblib.load(model_path)
                    
                    current_model_output = {}
                    predictions = model.predict(X_scaled)
                    current_model_output["predictions"] = predictions

                    if hasattr(model, 'predict_proba'):
                        try:
                            probabilities = model.predict_proba(X_scaled)
                            current_model_output["probabilities"] = probabilities
                        except Exception as e_proba:
                            print(f"Не удалось получить вероятности для модели '{model_file_name}': {e_proba}")
                            current_model_output["probabilities"] = f"Error retrieving probabilities: {e_proba}" # Сохраняем информацию об ошибке
                    else:
                        current_model_output["probabilities"] = "N/A" # Указываем, что вероятности недоступны

                    model_outputs[model_file_name] = current_model_output

                except Exception as e_model:
                    print(f"Ошибка при загрузке или предсказании моделью '{model_file_name}': {e_model}")
                    model_outputs[model_file_name] = {"predictions": f"Error: {e_model}", "probabilities": f"Error: {e_model}"} # Сохраняем информацию об ошибке
            
            if model_outputs:
                print("\nВсе предсказания собраны.")
            else:
                print("\nНе удалось получить предсказания ни от одной модели.")

        except FileNotFoundError as fnf_e:
            print(f"Завершение блока предсказаний из-за отсутствия файла: {fnf_e}")
        except Exception as e_main_pred:
            print(f"Произошла общая ошибка в блоке предсказаний: {e_main_pred}")
    
    return model_outputs



def get_analys(contract_address, chain):
    print(f"Получение исходного кода для контракта: {contract_address}...")
    main_file_path = get_contract_source_code(contract_address, chain)
    get_analysis_files(main_file_path, chain, contract_address)
    try:
        df = pd.read_csv("results.csv", skip_blank_lines=True, encoding='utf-8') # Читаем с кодировкой UTF-8
        print("Файл 'results.csv' успешно загружен.")
    except FileNotFoundError:
        print("Ошибка: Файл 'results.csv' не найден.")
        df = pd.DataFrame()
    except Exception as e:
        print(f"Ошибка при чтении файла 'results.csv': {e}")
        df = pd.DataFrame()

    df_final = get_data_to_predict(df)

    all_model_predictions = predict_data(df_final)
    
    if all_model_predictions:
        print("\n--- Результаты предсказаний всех моделей ---")
        for model_name, output in all_model_predictions.items():
            print(f"Модель: {model_name}")
            predictions_output = output.get('predictions')
            probabilities_output = output.get('probabilities')
            print(f"  Предсказания: {predictions_output}")
            print(f"  Вероятности: {probabilities_output}")
        print("--- Конец результатов предсказаний ---")
        return all_model_predictions
    else:
        print("\nПредсказания не были получены.")
        return {}
    
    # Здесь вы можете добавить код для возврата или дальнейшей обработки all_model_predictions
    # например, return all_model_predictions