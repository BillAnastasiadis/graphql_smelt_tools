import requests
import json
import sys

def flatten_response(data):
    if isinstance(data, dict):
        if "edges" in data and isinstance(data["edges"], list):
            return [flatten_response(edge["node"]) if isinstance(edge, dict) and "node" in edge
                    else flatten_response(edge)
                    for edge in data["edges"]]
        else:
            return {key: flatten_response(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [flatten_response(item) for item in data]
    else:
        return data

def get_request_json(request_id: int, flatten=True) -> dict:
    url = "https://smelt.suse.de/graphql"

    query = f"""\
        query getRequests {{
          requests(requestId: {request_id}) {{
            edges {{
              node {{
                requestId
                created
                endDate
                reviewSet {{
                  edges {{
                    node {{
                      assignedAt
                      reviewedAt
                      assignedTo {{
                        username
                      }}
                      assignedByUser {{
                        username
                      }}
                      assignedByGroup {{
                        name
                      }}
                    }}
                  }}
                }}
                references {{
                  edges {{
                    node {{
                      name
                    }}
                  }}
                }}
                incident {{
                  incidentId
                  packages {{
                    edges {{
                      node {{
                        name
                      }}
                    }}
                  }}
                  repositories {{
                        edges {{
                          node {{
                            name
                          }}
                        }}
                      }}
                }}
              }}
            }}
          }}
        }}
    """

    params = {
        "query": query,
        "operationName": "getRequests",
        "variables": "{}"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    if flatten:
        return flatten_response(response.json())
    return response.json()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            request_ids = [int(arg) for arg in sys.argv[1:]]
        except ValueError:
            sys.exit("All request IDs must be integers.")
    else:
        print("Please provide a request number")
        exit(1)

    for rid in request_ids:
        result = get_request_json(rid)
        print(f"Results for requestId {rid}:")
        print(json.dumps(result, indent=4))
        print("\n" + "="*80 + "\n")

