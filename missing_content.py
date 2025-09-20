    async def clear_tokens(self) -> bool:
        """Clear all stored tokens.

        Returns:
            bool: True if the tokens were cleared successfully, False otherwise
        """
        self._tokens = {}
        return await self.save_tokens()
