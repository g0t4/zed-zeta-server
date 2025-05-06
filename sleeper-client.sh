curl localhost:9000/test_sleeper_proxy

# run this and immediately ctrl-c
#  server logs will show:
#       INFO   127.0.0.1:61084 - "GET /test_sleeper HTTP/1.1" 200
# Checking if client is disconnected
# Sending event 0
# Client disconnected
# Request cancelled
#
# Client disconnected - is talking about curl being closed
# Request cancelled - is the upstream request to /test_sleeper

