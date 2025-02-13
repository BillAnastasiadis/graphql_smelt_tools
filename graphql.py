import requests
import json
import sys

url = "https://smelt.suse.de/graphql"
group_names = ['qam-teradata', 'qam-emergency', 'qam-virtualization', 'qam-sle', 'qam-ha', 'qam-kernel']

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
    
def get_all_request_ids(first=100, endDate_Gt="2014-01-01T00:00:00Z", detailed=False) -> list:
    """
    Iterates through all pages and returns a list of requests (id-only OR with full info, depending on the 'detailed' arg
    
    Parameters:
      - first: number of items per page. UPPER LIMIT IS 100
      - endDate_Gt: a DateTime string filter to only return requests with an endDate greater than this value.
                   Default is "2014-01-01T00:00:00Z".
      - detailed: if False (default), return a list of request IDs.
                  if True, return a list of full request nodes.
    """
    request_items = []
    after_cursor = None
    regex_pattern = "^(%s)$" % "|".join(group_names)

    if not detailed:
        fields = "requestId"
    else:
        fields = """
                requestId
                created
                endDate
                reviewSet {
                  edges {
                    node {
                      assignedAt
                      reviewedAt
                      assignedTo {
                        username
                      }
                      assignedByUser {
                        username
                      }
                      assignedByGroup {
                        name
                      }
                    }
                  }
                }
                references {
                  edges {
                    node {
                      name
                    }
                  }
                }
                incident {
                  incidentId
                  packages {
                    edges {
                      node {
                        name
                      }
                    }
                  }
                  repositories {
                    edges {
                      node {
                        name
                      }
                    }
                  }
                }
                """

    while True:
        if after_cursor is None:
            query = f"""\
                query getRequests {{
                  requests(first: {first}, review_AssignedByGroup_Name_Iregex: "{regex_pattern}", endDate_Gt: "{endDate_Gt}") {{
                    edges {{
                      node {{
                        {fields}
                      }}
                    }}
                    pageInfo {{
                      hasNextPage
                      endCursor
                    }}
                  }}
                }}
            """
        else:
            query = f"""\
                query getRequests {{
                  requests(first: {first}, after: "{after_cursor}", review_AssignedByGroup_Name_Iregex: "{regex_pattern}", endDate_Gt: "{endDate_Gt}") {{
                    edges {{
                      node {{
                        {fields}
                      }}
                    }}
                    pageInfo {{
                      hasNextPage
                      endCursor
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
        data = response.json()

        requests_data = data.get("data", {}).get("requests", {})
        edges = requests_data.get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            if not detailed:
                rid = node.get("requestId")
                if rid is not None:
                    request_items.append(rid)
            else:
                request_items.append(node)

        page_info = requests_data.get("pageInfo", {})
        if page_info.get("hasNextPage"):
            after_cursor = page_info.get("endCursor")
        else:
            break

    return flatten_response(request_items)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            request_ids = [int(arg) for arg in sys.argv[1:]]
            for rid in request_ids:
                result = get_request_json(rid)
                print(f"Results for requestId {rid}:")
                print(json.dumps(result, indent=4))
                print("\n" + "="*80 + "\n")
        except ValueError:
            sys.exit("All request IDs must be integers.")
    else:
        print("Please provide a request number for detailed query via get_request_json.")
    
    # Example Usage of function get_all_request_ids to ONLY get the ids. Import the function in your script and use it, changing endDate_Gt (don't forget the 'T00:00:00Z'!) and 'detailed' if you want
    # detailed = True will return not only the IDs, but all data that "get_request_json" returns
    all_ids = get_all_request_ids(first=100, endDate_Gt="2025-01-01T00:00:00Z", detailed=False)
    print("All request IDs:")
    print(json.dumps(all_ids, indent=4))
    print(len(all_ids))
    
    # For detailed results:
    all_details = get_all_request_ids(first=100, endDate_Gt="2025-01-01T00:00:00Z", detailed=True)
    print("Detailed request data:")
    print(json.dumps(all_details, indent=4))

