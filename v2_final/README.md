# Version 2 final results

- `analysis.json`: output of `python -m ledgershift.analyze_v2 --escalation v2_final/escalation_qwen2.5_14b_v3`.
- `escalation_qwen2.5_14b_v3/`: selective-escalation responses for all 1,200 v2 test statements (Qwen2.5 14B, prompt v3), merged from runs 42046603524, 42110254944 (records recovered from job logs after runner shutdowns), 42130193259, 42133160302 and 42137400068. Files are read in sorted order and later files override earlier ones by instance_id; the `shard_zz_*` files hold reruns of calls that failed. Seven statements timed out twice and keep their error records.
