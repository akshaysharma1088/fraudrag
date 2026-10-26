"""V7B correction: repeat full paired TAT-QA test benchmark with safe output limit.

Supersedes but DOES NOT delete the incomplete V7 result. Original V7
stopped at 81/128 calls because one response hit 250 output tokens. This
repeat uses 650 maximum output tokens uniformly across both policies.
"""
import tatqa_test_v7 as study

study.MAX_OUTPUT=650

if __name__=="__main__":
    study.main()
