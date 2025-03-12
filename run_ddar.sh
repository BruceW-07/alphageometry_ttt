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
set -x

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

echo $PYTHONPATH

PROBLEM_FILE="imo_ag_30.txt"
PROBLEM_NAME="translated_imo_2002_p2a"

python -m alphageometry \
--alsologtostderr \
--problems_file=$(pwd)/$PROBLEM_FILE \
--problem_name=$PROBLEM_NAME \
--mode=ddar \
# --out_file=output/ddar/$PROBLEM_NAME.txt \
"${DDAR_ARGS[@]}"

# python -m alphageometry \
# --alsologtostderr \
# --problems_file=$(pwd)/imo_ag_30.txt \
# --problem_name=translated_imo_2000_p1 \
# --mode=ddar \
# --out_file=output/ddar/translated_imo_2000_p1.txt \
# "${DDAR_ARGS[@]}"