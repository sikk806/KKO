from __future__ import annotations

import re
import unittest

from mypet_life_mcp.server import create_app


class ServerMetadataTests(unittest.IsolatedAsyncioTestCase):
    async def test_playmcp_tool_metadata(self):
        tools = await create_app().list_tools()

        self.assertGreaterEqual(len(tools), 3)
        self.assertLessEqual(len(tools), 10)
        for tool in tools:
            self.assertRegex(tool.name, re.compile(r"^[A-Za-z0-9_-]{1,128}$"))
            self.assertNotIn("kakao", tool.name.lower())
            self.assertIn("MyPet Life(마이펫 라이프)", tool.description)
            self.assertLessEqual(len(tool.description), 1024)
            self.assertTrue(tool.inputSchema)

            self.assertIsNotNone(tool.annotations)
            self.assertTrue(tool.annotations.title)
            self.assertIs(tool.annotations.readOnlyHint, True)
            self.assertIs(tool.annotations.destructiveHint, False)
            self.assertIs(tool.annotations.idempotentHint, True)
            self.assertIs(tool.annotations.openWorldHint, True)
