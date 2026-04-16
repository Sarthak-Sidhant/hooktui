import asyncio
import uuid
from datetime import datetime
from dnslib import DNSRecord, QTYPE, RR, A

class DNSProtocol(asyncio.DatagramProtocol):
    def __init__(self, tui_app):
        self.tui_app = tui_app

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        try:
            request = DNSRecord.parse(data)
            reply = request.reply()
            
            qname = request.q.qname
            qtype_int = request.q.qtype
            qtype = QTYPE.get(qtype_int, str(qtype_int))
            
            # Respond with 127.0.0.1 for all A record queries
            if qtype == "A":
                reply.add_answer(RR(qname, QTYPE.A, rdata=A("127.0.0.1"), ttl=60))
                
            self.transport.sendto(reply.pack(), addr)
            
            from hooktui.models import WebhookRequest, WebhookReceived
            
            webhook_req = WebhookRequest(
                id=str(uuid.uuid4()),
                method="DNS",
                url=f"dns://{qname}",
                headers={"Protocol": "UDP/DNS"},
                query_params={"qtype": qtype},
                body=request.toZone().decode("utf-8") if isinstance(request.toZone(), bytes) else str(request.toZone()),
                client_ip=addr[0]
            )
            self.tui_app.post_message(WebhookReceived(request=webhook_req))
        except Exception:
            pass

async def start_dns_server(tui_app, host="0.0.0.0", port=5333):
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DNSProtocol(tui_app),
        local_addr=(host, port)
    )
    return transport
