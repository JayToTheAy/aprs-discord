import logging
import asyncio
import aiohttp

import aprslib
from discord import Webhook, AllowedMentions, Object

WEBHOOK_URL = "https://example.com"
MENTION_PERMS = AllowedMentions(
    everyone=False, roles=False, replied_user=False, users=True
)
MY_CALL = "WY4RC"
MY_SSID = "67"


class APRSBridge:

    def __init__(self):
        self.AIS = aprslib.IS(
            f"{MY_CALL}-{MY_SSID}", passwd=str(aprslib.passcode(MY_CALL)), port=14580
        )
        self.AIS.set_filter(f"g/{MY_CALL}-{MY_SSID}")
        self.AIS.connect()
        self.AIS.consumer(callback=self.discord_notify, raw=False)

    def ack_packet(self, packet: dict):
        return_string = f"{MY_CALL}-{MY_SSID}>{packet["to"]}::{packet["from"]:9}:ack{packet["msgNo"]}\r\n"
        logging.debug(f"Ack Packet: `{return_string}`")
        self.AIS.sendall(return_string)

    async def discord_notify_async(self, packet: dict):
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                WEBHOOK_URL,
                session=session,
            )
            originator = packet.get("from")
            if originator:
                if packet.get("format") and packet.get("format") == "message":
                    text = packet.get("message_text")
                    if text:
                        await webhook.send(
                            content=text,
                            username=originator,
                            allowed_mentions=MENTION_PERMS,
                            thread=Object(id=1472079150687850557)
                        )
                    if packet.get("msgNo"):
                        logging.debug(f"Acking msg {packet['msgNo']}")
                        ack = self.ack_packet(packet)

    def discord_notify(self, packet: dict):
        """Synchronous wrapper that runs the async function"""
        asyncio.run(self.discord_notify_async(packet))


if __name__ == "__main__":
    aprs_bridge = APRSBridge()
