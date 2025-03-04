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
set -e
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
    
    # Process JGEX problems
    while read -r problem; do
        problem_sanitized=$(echo "${problem}" | tr '/' '_')  # 将 / 替换为 _
        out_file="output/${mode}/jgex/${problem_sanitized}.txt"

        python -m alphageometry \
        --alsologtostderr \
        --problems_file=$(pwd)/jgex_ag_231.txt \
        --problem_name="$problem" \
        --mode=$mode \
        --out_file=${out_file} \
        "${DDAR_ARGS[@]}" \
        "${SEARCH_ARGS[@]}" \
        "${LM_ARGS[@]}"
    done < <(get_problem_names "jgex_ag_231.txt")
    
    # Process IMO problems
    while read -r problem; do
        python -m alphageometry \
        --alsologtostderr \
        --problems_file=$(pwd)/imo_ag_30.txt \
        --problem_name="$problem" \
        --mode=$mode \
        --out_file="output/${mode}/imo/${problem}.txt" \
        "${DDAR_ARGS[@]}" \
        "${SEARCH_ARGS[@]}" \
        "${LM_ARGS[@]}"
    done < <(get_problem_names "imo_ag_30.txt")
done

# Count results
# echo "Results summary:"
# echo "AlphaGeometry mode:"
# echo "IMO problems: $(ls output/alphageometry/imo | wc -l)"
# echo "JGEX problems: $(ls output/alphageometry/jgex | wc -l)"
# echo "DDAR mode:"
# echo "IMO problems: $(ls output/ddar/imo | wc -l)"
# echo "JGEX problems: $(ls output/ddar/jgex | wc -l)"

echo "Results summary:"
echo "---------------------------------"
echo "|           | IMO problems | JGEX problems |"
echo "---------------------------------"
echo "| AlphaGeometry | $(ls output/alphageometry/imo | wc -l)          | $(ls output/alphageometry/jgex | wc -l)           |"
echo "---------------------------------"
echo "| DDAR         | $(ls output/ddar/imo | wc -l)          | $(ls output/ddar/jgex | wc -l)           |"
echo "---------------------------------"

