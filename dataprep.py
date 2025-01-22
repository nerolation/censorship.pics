from datetime import datetime
import pandas as pd
import os
from google.cloud import bigquery

DATA = "data/"

if not os.path.isdir(DATA):
    os.mkdir(DATA)

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


CREATE OR REPLACE TABLE `ethereum-data-nero.eth.9_tornado_in_mev_censorship` AS
SELECT AA.*,  BB.txs FROM
(SELECT DISTINCT AAA.block_number, AAA.slot, AAA.relay, AAA.builder, AAA.proposer_pubkey, IFNULL(BBB.name, AAA.validator) validator FROM `ethereum-data-nero.eth.mevboost_db` AAA
LEFT JOIN `ethereum-data-nero.eth.lido_validator_db` BBB on AAA.proposer_pubkey = BBB.pubkey) AA

INNER JOIN (
  SELECT A.block_number, count(distinct B.txhash) txs FROM (
    SELECT DISTINCT block_number, tx_hash FROM `ethereum-data-nero.eth.mevboost_txs` 
    UNION ALL
    SELECT DISTINCT block_number, tx_hash  FROM `ethereum-data-nero.eth.non_mevboost_txs`) A
  INNER JOIN (
    SELECT txhash FROM `ethereum-data-nero.eth.ofaced_txs`# WHERE contract != "torn"
  ) B ON B.txhash = A.tx_hash
  GROUP BY block_number
) BB ON AA.block_number = BB.block_number
WHERE BB.txs > 0 
and slot not in (
  SELECT distinct orphaned_slot FROM (
    SELECT distinct A.block_number, min(A.slot) orphaned_slot FROM 
    (SELECT slot, block_number FROM `ethereum-data-nero.eth.mevboost_empty_filled` ) A
    LEFT JOIN (
      SELECT slot, block_number FROM `ethereum-data-nero.eth.mevboost_empty_filled`
    ) B on A.block_number = B.block_number
    WHERE A.slot = B.slot-1
    group by A.block_number
    )
    order by orphaned_slot desc
)
and AA.slot != 6611105 and AA.slot != 6622529 # manual fix for blocknative
ORDER BY block_number; 

###############


CREATE OR REPLACE TABLE `ethereum-data-nero.eth.9_tornado_validator_stats_censorship` AS
SELECT * FROM (
  SELECT validator, count(validator) blocks, sum(txs) txs, "total" as frame FROM `ethereum-data-nero.eth.9_tornado_in_mev_censorship` GROUP BY validator
  UNION ALL
  SELECT validator, count(validator) blocks, sum(txs) txs, "24h" FROM `ethereum-data-nero.eth.9_tornado_in_mev_censorship` 
  WHERE slot > (
    (
      SELECT MAX(slot) FROM `ethereum-data-nero.eth.9_tornado_in_mev_censorship`
    ) - 86400/12
  )
  GROUP BY validator
  UNION ALL
  SELECT validator, count(validator) blocks, sum(txs) txs, "14d" FROM `ethereum-data-nero.eth.9_tornado_in_mev_censorship` 
  WHERE slot > (
    (
      SELECT MAX(slot) FROM `ethereum-data-nero.eth.9_tornado_in_mev_censorship`
    ) - 86400*14/12
  )
  GROUP BY validator
  UNION ALL
  SELECT validator, count(validator) blocks, sum(txs) txs, "30d" FROM `ethereum-data-nero.eth.9_tornado_in_mev_censorship` 
  WHERE slot > (
    (
      SELECT MAX(slot) FROM `ethereum-data-nero.eth.9_tornado_in_mev_censorship`
    ) - 86400*30/12
  )
  GROUP BY validator
  UNION ALL
  SELECT validator, blocks, txs, "all_blocks" FROM (
    SELECT IFNULL(BBB.name, AAA.validator) validator, count(validator) blocks, 0 txs FROM `ethereum-data-nero.eth.mevboost_db` AAA
    LEFT JOIN `ethereum-data-nero.eth.lido_validator_db` BBB on AAA.proposer_pubkey = BBB.pubkey
    GROUP BY validator
  )
  UNION ALL
  SELECT validator, blocks, txs, "all_blocks_30d" FROM (
    SELECT IFNULL(BBB.name, AAA.validator) validator, count(validator) blocks, 0 txs FROM `ethereum-data-nero.eth.mevboost_db` AAA
    LEFT JOIN `ethereum-data-nero.eth.lido_validator_db` BBB on AAA.proposer_pubkey = BBB.pubkey
    where TIMESTAMP_TRUNC(date, DAY) BETWEEN TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)) AND CURRENT_TIMESTAMP()
    GROUP BY validator
  )
)
WHERE not STARTS_WITH(validator, "0x")
ORDER BY validator DESC, frame DESC, blocks DESC;


#####################



CREATE OR REPLACE TABLE `ethereum-data-nero.eth.3_validators_over_time_censorship` AS
  SELECT 
  FORMAT_TIMESTAMP("%F", `date`) AS `timestamp`,
  IFNULL(BBB.name, AAA.validator) validator,
  count(distinct slot) slot
FROM `ethereum-data-nero.eth.mevboost_db`   AAA
LEFT JOIN `ethereum-data-nero.eth.lido_validator_db` BBB on AAA.proposer_pubkey = BBB.pubkey
where not STARTS_WITH(validator, "0x") and validator != "missed"

GROUP BY `timestamp`, validator


"""

def run_bq_job():
    print("running queries for validators...")
    client.query(query)
    print("finished bq job")
    
    
client = bigquery.Client()
run_bq_job()


QUERY = """
SELECT {}
FROM {}
{}
"""

def build_query(select, dataset, appendix=""):
    return QUERY.format(select, dataset, appendix)

def slot_to_time(slot):
    timestamp = 1606824023 + slot * 12
    dt_object = datetime.utcfromtimestamp(timestamp)
    formatted_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time








try:
    entries = pd.read_parquet(DATA+"tornado_blocks.parquet")
    maxslot = entries["slot"].max()
    maxslot
except:
    entries = pd.DataFrame()
    maxslot = 0
    
query = f"""SELECT distinct aa.slot, aa.builder, aa.relay, aa.validator, 
IF(bb.txs > 0, 1,0) touched_sanctioned_address #1/IF(CC.counts=0, 1, CC.counts) counts
FROM `ethereum-data-nero.eth.mevboost_db` aa LEFT JOIN
`ethereum-data-nero.eth.9_tornado_in_mev_censorship` bb on aa.slot = bb.slot 
#LEFT JOIN  (
#  SELECT slot, block_hash, COUNT(DISTINCT relay) AS counts
#  FROM `ethereum-data-nero.eth.mevboost_db`
#  where relay is not null
#  GROUP BY slot, block_hash
#) CC ON aa.slot = CC.slot
where aa.slot > {maxslot}
"""

query = f"""SELECT distinct aa.slot, aa.builder, aa.relay, aa.validator, IF(bb.txs > 0, 1,0) touched_sanctioned_address FROM `ethereum-data-nero.eth.mevboost_db` aa LEFT JOIN
`ethereum-data-nero.eth.9_tornado_in_mev_censorship` bb on aa.slot = bb.slot 
where aa.slot > {maxslot}"""

df = pd.read_gbq(query)
df["timestamp"] = df["slot"].apply(lambda x: slot_to_time(x))
df = pd.concat([entries, df], ignore_index=True)
#df["counts"] = df["counts"].fillna(1)
df.fillna("non Mev-Boost", inplace=True)
df.to_parquet(DATA + "tornado_blocks.parquet", index=False)


#df = entries
df_daily_share=[]
df['timestamp'] = pd.to_datetime(df['timestamp'])

relay_manual_started_censoring = {"2022-09-15 00:00:00": "flashbots", 
                                  "2022-09-16 00:00:00": "bloxroute (regulated)", 
                                  "2022-09-17 00:00:00": "eden", 
                                  "2022-09-18 00:00:00": "blocknative", 
                                  "2023-12-18 00:00:00": "bloxroute (max profit)"}

NO_CENSORSHIP_AS_OF = "2025-01-22 00:00:00"
for entity in ["validator", "relay", "builder"]:
    CS = True
    print(f"\n{entity}")
    df.sort_values(by=['timestamp', entity], inplace=True)
    data = []
    data2 = []
    largest = df.groupby(entity)["slot"].count().sort_values(ascending=False).reset_index()[entity].tolist()[:30]
    _df = df[df[entity].isin(largest)].copy()
    as_of_now_censoring = []
    for date in pd.date_range(_df['timestamp'].min().date(), _df['timestamp'].max().date()):
        if date == NO_CENSORSHIP_AS_OF:
            CS = True #False
        
        print(date, end="\r")
        if entity == "relay":
            if str(date) in relay_manual_started_censoring.keys():
                print(f"adding {relay_manual_started_censoring[str(date)]} to censoring entities as of {str(date)}")
                as_of_now_censoring.append(relay_manual_started_censoring[str(date)])
        start_date = date - pd.Timedelta(days=29)
        mask = (_df['timestamp'] >= start_date) & (_df['timestamp'] <= date)
        mask2 = (_df['timestamp'] >= date - pd.Timedelta(days=1)) & (_df['timestamp'] <= date)
        df_filtered = _df[mask].copy()
        df_filtered2 = _df[mask2].copy()
        if len(df_filtered2) == 0:
            continue
        avg_incl = df_filtered["touched_sanctioned_address"].mean()*100
        a = df_filtered.groupby(entity)["slot"].count().sort_index()
        b = df_filtered.groupby(entity)["touched_sanctioned_address"].sum().sort_index()
        a = a.reset_index()
        b = b.reset_index()
        a["percentage"] = b["touched_sanctioned_address"]/a["slot"]*100
        censoring = a.apply(lambda x: x[entity] if x["percentage"] < avg_incl/4 and x["slot"] > 100 else None, axis=1)
        censoring = list(censoring.dropna())
        censoring = list(set(censoring + as_of_now_censoring))
        if not CS:
            censoring = list()
        df_filtered2["censoring"] = df_filtered2[entity].isin(censoring).astype(int)
        gg = df_filtered2.groupby("censoring")["slot"].count()
        #gg = df_filtered2.groupby("censoring")["counts"].sum()/df_filtered2.groupby("censoring")["counts"].sum().sum()*100
        #print(date, int(gg.iloc[0]), int(gg.iloc[1]))
        #data.loc[len(data),("date", "censoring", "slots")] = (date, "censoring", int(gg.iloc[0]))  
        data.append((date, "non-censoring", int(gg.iloc[0])))
        if len(gg) > 1:
            data.append((date, "censoring", int(gg.iloc[1])))
        else:
            data.append((date, "censoring", 0))

    data = pd.DataFrame(data, columns=["date", "censoring", "slots"])
    _data = pd.merge(data, data.groupby("date")["slots"].sum().reset_index(), on="date")
    _data["Share_of_Blocks"] = _data["slots_x"]/_data["slots_y"]*100
    _data = _data.drop(["slots_x", "slots_y"], axis=1)
    _data.to_csv(DATA + entity+"_censorship_share.csv", index=False)








#query = """
#SELECT *, IF(tc_blocks30/all_blocks30 < 0.0090, 1, 0) censoring FROM (
#
#SELECT A.relay as entity, "relay" as category, IFNULL(tc_blocks30, 0) tc_blocks30, all_blocks30 from
#(SELECT relay, blocks as all_blocks30 FROM `ethereum-data-nero.eth.9_tornado_relay_stats` where frame = "all_blocks_30d"
#) A LEFT JOIN (
#  SELECT relay, blocks as tc_blocks30 FROM `ethereum-data-nero.eth.9_tornado_relay_stats` where frame = "30d"
#) B on A.relay = B.relay
#UNION ALL
#SELECT A.builder, "builder" as category, IFNULL(tc_blocks30, 0) tc_blocks30, all_blocks30 from
#(SELECT builder, blocks as all_blocks30 FROM `ethereum-data-nero.eth.9_tornado_builder_stats` where frame = "all_blocks_30d"
#) A LEFT JOIN (
#  SELECT builder, blocks as tc_blocks30 FROM `ethereum-data-nero.eth.9_tornado_builder_stats` where frame = "30d"
#) B on A.builder = B.builder
#UNION ALL
#SELECT A.validator, "validator" as category, IFNULL(tc_blocks30, 0) tc_blocks30, all_blocks30 from
#(SELECT validator, blocks as all_blocks30 FROM `ethereum-data-nero.eth.9_tornado_validator_stats_censorship` where frame = "all_blocks_30d"
#) A LEFT JOIN (
#  SELECT validator, blocks as tc_blocks30 FROM `ethereum-data-nero.eth.9_tornado_validator_stats_censorship` where frame = "30d"
#) B on A.validator = B.validator)
#"""
#df_censoring = pd.read_gbq(query)
#
#df_censoring.to_csv(DATA + "censorship_stats.csv", index=False)

#DS = "ethereum-data-nero.eth.3_relays_over_time"
#query = build_query("timestamp, relay, slot", DS, "ORDER BY slot DESC")
#df = pd.read_gbq(query)
#df.to_csv("relays_over_time.csv", index=False)
#DS = "ethereum-data-nero.eth.3_builders_over_time"
#query = build_query("timestamp, builder, slot", DS, "ORDER BY slot DESC")
#df = pd.read_gbq(query)
#df.to_csv("builders_over_time.csv", index=False)
#DS = "ethereum-data-nero.eth.3_validators_over_time_censorship"
#query = build_query("timestamp, validator, slot", DS, "ORDER BY slot DESC")
#df = pd.read_gbq(query)
#df.to_csv("validators_over_time_censorship.csv", index=False)
#

query = """SELECT AA.relay, IFNULL(BB.blocks, 0) non_censored_blocks, AA.blocks all_blocks, IFNULL(BB.blocks/AA.blocks* 100, 0)  share 
FROM (
  SELECT distinct relay, blocks  FROM `ethereum-data-nero.eth.9_tornado_relay_stats` 
  WHERE frame = "all_blocks_30d" 
) AS AA
LEFT JOIN (
  SELECT distinct relay, blocks  FROM `ethereum-data-nero.eth.9_tornado_relay_stats`
  WHERE frame = "30d"
) AS BB
ON AA.relay = BB.relay
order by share desc
"""
df = pd.read_gbq(query)
df.to_csv(DATA + "relay_stats.csv", index=False)

query = """SELECT AA.builder, IFNULL(BB.blocks, 0) non_censored_blocks, AA.blocks all_blocks, IFNULL(BB.blocks/AA.blocks* 100, 0)  share 
FROM (
  SELECT distinct builder, blocks FROM `ethereum-data-nero.eth.9_tornado_builder_stats` 
  WHERE frame = "all_blocks_30d" 
) AS AA
LEFT JOIN (
  SELECT distinct builder, blocks  FROM `ethereum-data-nero.eth.9_tornado_builder_stats`
  WHERE frame = "30d"
) AS BB
ON AA.builder = BB.builder
order by share desc
"""
df = pd.read_gbq(query)
df.to_csv(DATA + "builder_stats.csv", index=False)

query = """SELECT AA.validator, IFNULL(BB.blocks, 0) non_censored_blocks, AA.blocks all_blocks, IFNULL(BB.blocks/AA.blocks* 100, 0)  share 
FROM (
  SELECT distinct validator, blocks  FROM `ethereum-data-nero.eth.9_tornado_validator_stats_censorship` 
  WHERE frame = "all_blocks_30d" 
) AS AA
LEFT JOIN (
  SELECT distinct validator, blocks  FROM `ethereum-data-nero.eth.9_tornado_validator_stats_censorship`
  WHERE frame = "30d"
) AS BB
ON AA.validator = BB.validator
order by share desc
"""
df = pd.read_gbq(query)
df.to_csv(DATA + "validator_stats.csv", index=False)

print("finished")
