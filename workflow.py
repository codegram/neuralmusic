import spell.client

# Create a client
client = spell.client.from_environment()

r = client.runs.new(
    command="python data.py; rm -fr outputs",
    conda_file="conda.yml",
    attached_resources={"uploads/midi": "midi"},
    idempotent=True,
)
print("waiting for run {} to complete".format(r.id))
r.wait_status(client.runs.COMPLETE)
