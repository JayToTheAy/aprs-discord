import logging
import asyncio
import aiohttp

import aprslib
from discord import Webhook, Object

from .options import MY_CALL, MY_SSID, WEBHOOK_URL, TARGET_THREAD, MENTION_PERMS
from .call_avatars import CALLS


class APRSBridge:

    def __init__(self):
        self.most_recent_message = dict()

        self.AIS = aprslib.IS(
            f"{MY_CALL}-{MY_SSID}", passwd=str(aprslib.passcode(MY_CALL)), port=14580
        )
        self.AIS.set_filter(f"g/{MY_CALL}-{MY_SSID}")
        self.AIS.connect()
        self.AIS.consumer(callback=self.discord_notify, raw=False)

    def ack_packet(self, packet: dict[str, str]):
        return_string = f"{MY_CALL}-{MY_SSID}>{packet["to"]}::{packet["from"]:9}:ack{packet["msgNo"]}\r\n"
        logging.debug(f"Ack Packet: `{return_string}`")
        self.AIS.sendall(return_string)

    async def discord_notify_async(self, packet: dict[str, str]):
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                WEBHOOK_URL,
                session=session,
            )
            originator = packet.get("from")
            if originator:
                originator.split(",")
                avatar_url = CALLS[originator[0]]
                if packet.get("format") and packet.get("format") == "message":
                    text = packet.get("message_text")
                    if text:
                        await webhook.send(
                            content=text,
                            username=originator,
                            allowed_mentions=MENTION_PERMS,
                            silent=True,
                            thread=Object(id=TARGET_THREAD),
                            avatar_url=avatar_url,
                        )
                    if packet.get("msgNo"):
                        logging.debug(f"Acking msg {packet['msgNo']}")
                        ack = self.ack_packet(packet)

    def discord_notify(self, packet: dict):
        """Synchronous wrapper that runs the async function"""
        asyncio.run(self.discord_notify_async(packet))


if __name__ == "__main__":
    aprs_bridge = APRSBridge()
