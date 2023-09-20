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

def slot_to_time(slot):
    timestamp = 1606824023 + slot * 12
    dt_object = datetime.utcfromtimestamp(timestamp)
    formatted_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


def set_google_credentials(CONFIG, GOOGLE_CREDENTIALS):
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    except:
        print(f"setting google credentials as global variable...")
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CONFIG \
        + GOOGLE_CREDENTIALS or input("No Google API credendials file provided." 
        + "Please specify path now:\n")
        
set_google_credentials("./config/","google-creds.json")






try:
    entries = pd.read_parquet("tornado_blocks.parquet")
    maxslot = entries["slot"].max()
    maxslot
except:
    entries = pd.DataFrame()
    maxslot = 0
    
query = f"""SELECT distinct aa.slot, aa.builder, aa.relay, aa.validator, IF(bb.txs > 0, 1,0) touched_sanctioned_address FROM `ethereum-data-nero.eth.mevboost_db` aa LEFT JOIN
`ethereum-data-nero.eth.9_tornado_in_mev_censorship` bb on aa.slot = bb.slot 
where aa.slot > {maxslot}
"""
df = pd.read_gbq(query)
df["timestamp"] = df["slot"].apply(lambda x: slot_to_time(x))
df = pd.concat([entries, df], ignore_index=True)
df.fillna("non Mev-Boost", inplace=True)
df.to_parquet("tornado_blocks.parquet", index=False)


df = entries
df_daily_share=[]
df['timestamp'] = pd.to_datetime(df['timestamp'])

for entity in ["validator", "relay", "builder"]:
    print(f"\n{entity}")
    df.sort_values(by=['timestamp', entity], inplace=True)
    data = []
    largest = df.groupby(entity)["slot"].count().sort_values(ascending=False).reset_index()[entity].tolist()[:30]
    _df = df[df[entity].isin(largest)].copy()
    for date in pd.date_range(_df['timestamp'].min().date(), _df['timestamp'].max().date()):
        
        print(date, end="\r")
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
        
        censoring = a.apply(lambda x: x[entity] if x["percentage"] < avg_incl/2 and x["slot"] > 100 else None, axis=1)
        df_filtered2["censoring"] = df_filtered2[entity].isin(censoring).astype(int)
        gg = df_filtered2.groupby("censoring")["slot"].count()
        
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
    _data.to_csv(entity+"_censorship_share.csv", index=False)








query = """
SELECT *, IF(tc_blocks30/all_blocks30 < 0.0090, 1, 0) censoring FROM (

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
df.to_csv("relay_stats.csv", index=False)

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
df.to_csv("builder_stats.csv", index=False)

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
df.to_csv("validator_stats.csv", index=False)

print("finished")