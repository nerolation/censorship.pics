from datetime import datetime
import pandas as pd
import os


QUERY = """
SELECT {}
FROM {}
{}
"""

def build_query(select, dataset, appendix=""):
    return QUERY.format(select, dataset, appendix)


def set_google_credentials(CONFIG, GOOGLE_CREDENTIALS):
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    except:
        print(f"setting google credentials as global variable...")
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CONFIG \
        + GOOGLE_CREDENTIALS or input("No Google API credendials file provided." 
        + "Please specify path now:\n")
        
set_google_credentials("./config/","google-creds.json")

query = """
SELECT *, IF(tc_blocks30/all_blocks30 < 0.01, 1, 0) censoring FROM (

SELECT A.relay as entity, "relay" as category, IFNULL(tc_blocks30, 0) tc_blocks30, all_blocks30 from
(SELECT relay, blocks as all_blocks30 FROM `ethereum-data-nero.eth.9_tornado_relay_stats` where frame = "all_blocks_30d"
) A LEFT JOIN (
  SELECT relay, blocks as tc_blocks30 FROM `ethereum-data-nero.eth.9_tornado_relay_stats` where frame = "30d"
) B on A.relay = B.relay
UNION ALL
SELECT A.builder, "builder" as category, IFNULL(tc_blocks30, 0) tc_blocks30, all_blocks30 from
(SELECT builder, blocks as all_blocks30 FROM `ethereum-data-nero.eth.9_tornado_builder_stats` where frame = "all_blocks_30d"
) A LEFT JOIN (
  SELECT builder, blocks as tc_blocks30 FROM `ethereum-data-nero.eth.9_tornado_builder_stats` where frame = "30d"
) B on A.builder = B.builder
UNION ALL
SELECT A.validator, "validator" as category, IFNULL(tc_blocks30, 0) tc_blocks30, all_blocks30 from
(SELECT validator, blocks as all_blocks30 FROM `ethereum-data-nero.eth.9_tornado_validator_stats_censorship` where frame = "all_blocks_30d"
) A LEFT JOIN (
  SELECT validator, blocks as tc_blocks30 FROM `ethereum-data-nero.eth.9_tornado_validator_stats_censorship` where frame = "30d"
) B on A.validator = B.validator)
"""
df_censoring = pd.read_gbq(query)

df_censoring.to_csv("censorship_stats.csv", index=False)

DS = "ethereum-data-nero.eth.3_relays_over_time"
query = build_query("timestamp, relay, slot", DS, "ORDER BY slot DESC")
df = pd.read_gbq(query)
df.to_csv("relays_over_time.csv", index=False)
DS = "ethereum-data-nero.eth.3_builders_over_time"
query = build_query("timestamp, builder, slot", DS, "ORDER BY slot DESC")
df = pd.read_gbq(query)
df.to_csv("builders_over_time.csv", index=False)
DS = "ethereum-data-nero.eth.3_validators_over_time_censorship"
query = build_query("timestamp, validator, slot", DS, "ORDER BY slot DESC")
df = pd.read_gbq(query)
df.to_csv("validators_over_time_censorship.csv", index=False)


query = """SELECT AA.relay, IFNULL(BB.blocks, 0) non_censored_blocks, AA.blocks all_blocks, IFNULL(BB.blocks/AA.blocks* 100, 0)  share 
FROM (
  SELECT * FROM `ethereum-data-nero.eth.9_tornado_relay_stats` 
  WHERE frame = "all_blocks_30d" 
) AS AA
LEFT JOIN (
  SELECT * FROM `ethereum-data-nero.eth.9_tornado_relay_stats`
  WHERE frame = "30d"
) AS BB
ON AA.relay = BB.relay
order by share desc
"""
df = pd.read_gbq(query)
df.to_csv("relay_stats.csv", index=False)

query = """SELECT AA.builder, IFNULL(BB.blocks, 0) non_censored_blocks, AA.blocks all_blocks, IFNULL(BB.blocks/AA.blocks* 100, 0)  share 
FROM (
  SELECT * FROM `ethereum-data-nero.eth.9_tornado_builder_stats` 
  WHERE frame = "all_blocks_30d" 
) AS AA
LEFT JOIN (
  SELECT * FROM `ethereum-data-nero.eth.9_tornado_builder_stats`
  WHERE frame = "30d"
) AS BB
ON AA.builder = BB.builder
order by share desc
"""
df = pd.read_gbq(query)
df.to_csv("builder_stats.csv", index=False)

query = """SELECT AA.validator, IFNULL(BB.blocks, 0) non_censored_blocks, AA.blocks all_blocks, IFNULL(BB.blocks/AA.blocks* 100, 0)  share 
FROM (
  SELECT * FROM `ethereum-data-nero.eth.9_tornado_validator_stats_censorship` 
  WHERE frame = "all_blocks_30d" 
) AS AA
LEFT JOIN (
  SELECT * FROM `ethereum-data-nero.eth.9_tornado_validator_stats_censorship`
  WHERE frame = "30d"
) AS BB
ON AA.validator = BB.validator
order by share desc
"""
df = pd.read_gbq(query)
df.to_csv("validator_stats.csv", index=False)

print("finished")