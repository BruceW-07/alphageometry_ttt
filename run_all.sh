# Copyright 2023 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# !/bin/bash
set +e
ERROR_LOG="error_log.txt"
echo "Error Log - $(date)" > "$ERROR_LOG"
TIME_LOG="time_log.txt"
echo "Time Log - $(date)" > "$TIME_LOG"
TIMEOUT=7200  # 2 hours in seconds

# Function to run command with timeout and time tracking
run_with_timeout() {
    local start_time=$(date +%s)
    local problem=$1
    local mode=$2
    local out_file=$3
    shift 3

    if timeout $TIMEOUT "$@"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        echo "[$(date)] $mode - $problem: Completed in $duration seconds" >> "$TIME_LOG"
        return 0
    else
        local exit_code=$?
        if [ $exit_code -eq 124 ]; then  # timeout exit code
            echo "[$(date)] $mode - $problem: Timed out after $TIMEOUT seconds" >> "$TIME_LOG"
        fi
        return $exit_code
    fi
}

# set -x

# virtualenv -p python3 .
source ./bin/activate

# pip install --require-hashes -r requirements.txt

# gdown --folder https://bit.ly/alphageometry
DATA=ag_ckpt_vocab

MELIAD_PATH=meliad_lib/meliad
# mkdir -p $MELIAD_PATH
# git clone https://github.com/google-research/meliad $MELIAD_PATH
export PYTHONPATH=$PYTHONPATH:$MELIAD_PATH

DDAR_ARGS=(
  --defs_file=$(pwd)/defs.txt \
  --rules_file=$(pwd)/rules.txt \
);

BATCH_SIZE=32
BEAM_SIZE=512
DEPTH=16

SEARCH_ARGS=(
  --beam_size=$BEAM_SIZE
  --search_depth=$DEPTH
)

LM_ARGS=(
  --ckpt_path=$DATA \
  --vocab_path=$DATA/geometry.757.model \
  --gin_search_paths=$MELIAD_PATH/transformer/configs \
  --gin_file=base_htrans.gin \
  --gin_file=size/medium_150M.gin \
  --gin_file=options/positions_t5.gin \
  --gin_file=options/lr_cosine_decay.gin \
  --gin_file=options/seq_1024_nocache.gin \
  --gin_file=geometry_150M_generate.gin \
  --gin_param=DecoderOnlyLanguageModelGenerate.output_token_losses=True \
  --gin_param=TransformerTaskConfig.batch_size=$BATCH_SIZE \
  --gin_param=TransformerTaskConfig.sequence_length=128 \
  --gin_param=Trainer.restore_state_variables=False
);

# # Function to get problem names from file
get_problem_names() {
    local file=$1
    sed -n '1~2p' "$file"  # Get odd-numbered lines
}

# Function to get the first line problem name from file
# get_problem_names() {
#     local file=$1
#     sed -n '1p' "$file"  # Get the first line
# }

# Create output directories
mkdir -p output/alphageometry/imo
mkdir -p output/alphageometry/jgex
mkdir -p output/ddar/imo
mkdir -p output/ddar/jgex

# Process IMO problems
for mode in "alphageometry" "ddar"; do
    echo "Processing mode: $mode"
    
    # Process IMO problems
    while read -r problem; do
        out_file="output/${mode}/imo/${problem}.txt"

        # 检查输出文件是否已存在
        if [ -f "${out_file}" ]; then
            echo "Skipping IMO problem ${problem} (output file already exists)"
            continue
        fi

        echo "Processing IMO problem: $problem"
        if ! run_with_timeout "$problem" "$mode" "$out_file" python -m alphageometry \
            --alsologtostderr \
            --problems_file=$(pwd)/imo_ag_30.txt \
            --problem_name="$problem" \
            --mode=$mode \
            --out_file="$out_file" \
            "${DDAR_ARGS[@]}" \
            "${SEARCH_ARGS[@]}" \
            "${LM_ARGS[@]}"; then
            echo "[$(date)] Error processing IMO problem: $problem in $mode mode" >> "$ERROR_LOG"
        fi
    done < <(get_problem_names "imo_ag_30.txt")
    
    # Process JGEX problems
    while read -r problem; do
        problem_sanitized=$(echo "${problem}" | tr '/' '_')  # 将 / 替换为 _
        out_file="output/${mode}/jgex/${problem_sanitized}.txt"

        # 检查输出文件是否已存在
        if [ -f "${out_file}" ]; then
            echo "Skipping JGEX problem ${problem} (output file already exists)"
            continue
        fi

        echo "Processing JGEX problem: $problem"
        if ! run_with_timeout "$problem" "$mode" "$out_file" python -m alphageometry \
            --alsologtostderr \
            --problems_file=$(pwd)/jgex_ag_231.txt \
            --problem_name="$problem" \
            --mode=$mode \
            --out_file=${out_file} \
            "${DDAR_ARGS[@]}" \
            "${SEARCH_ARGS[@]}" \
            "${LM_ARGS[@]}"; then
            echo "[$(date)] Error processing JGEX problem: $problem in $mode mode" >> "$ERROR_LOG"
        fi
    done < <(get_problem_names "jgex_ag_231.txt")
done

echo "Results summary:"
echo "---------------------------------"
echo "|           | IMO problems | JGEX problems |"
echo "---------------------------------"
echo "| AlphaGeometry | $(ls output/alphageometry/imo | wc -l)          | $(ls output/alphageometry/jgex | wc -l)           |"
echo "---------------------------------"
echo "| DDAR         | $(ls output/ddar/imo | wc -l)          | $(ls output/ddar/jgex | wc -l)           |"
echo "---------------------------------"

echo ""
echo "Time Summary:"
echo "------------"
echo "Check $TIME_LOG for detailed timing information"
echo "Timed out problems: $(grep -c "Timed out" "$TIME_LOG")"

echo ""
echo "Error Summary:"
echo "-------------"
echo "Total errors: $(grep -c "Error processing" "$ERROR_LOG")"
echo "Check $ERROR_LOG for detailed error information"

