import spell.client

# Create a client
client = spell.client.from_environment()

r = client.runs.new(
    command="mkdir -p data && tar -zxf midi/midi.tar.gz -C data && python data.py; rm -fr data",
    pip_packages=["fastparquet", "pandas", "music21", "fastprogress"],
    attached_resources={
        "uploads/midi": "midi"
    },
    idempotent=True
)
print("waiting for run {} to complete".format(r.id))
r.wait_status(client.runs.COMPLETE)