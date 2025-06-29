# FlashBar - ./modules/Relevancy.py -> Dataclass for the relevance of a file.
# Copyright (C) 2025  Florian, Floerianc on Github (https://www.github.com/floerianc)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from dataclasses import (
    dataclass,
    field
)
from datetime import (
    datetime,
    timedelta
)
from typing import Union, List

@dataclass
class Relevance:
    path: str
    clicks: List[datetime] = field(default_factory=list)
    
    @property
    def accesses(self) -> int:
        return len(self.clicks)
    
    @property
    def lastAccess(self) -> Union[datetime, None]:
        if len(self.clicks) == 0:
            return None
        return self.clicks[-1]
    
    @property
    def isFrequent(self) -> bool:
        accessesInWeek = 0
        today = datetime.today()
        
        for click in self.clicks:
            if click >= (today - timedelta(weeks=1)):
                accessesInWeek += 1
        return accessesInWeek >= 10
    
    @property
    def relevanceScore(self) -> int:
        rating = self.accesses
        if rating == 0:
            return 0
        
        if self.lastAccess:
            LastAccess = self.lastAccess
            timeDifference = datetime.today() - LastAccess
            rating -= timeDifference.days
        
        if self.clicks:
            # >10x in 7d
            if self.isFrequent:
                rating *= 4
        return rating
    
    def toDict(self) -> dict:
        return {
            'path': self.path,
            'clicks': [dt.isoformat() for dt in self.clicks]
        }
    
    @classmethod
    def fromDict(cls, data: dict) -> 'Relevance':
        return cls(
            path = data["path"],
            clicks = [datetime.fromisoformat(dt) for dt in data.get("clicks", [])]
        )


if __name__ == "__main__":
    dummyObj = Relevance(
        "C:\\hello.txt",
        [
            datetime(2024, 6, 26, 11, 30, 0),
            datetime(2025, 6, 26, 12, 30, 0),
            datetime(2025, 6, 26, 13, 30, 0),
            datetime(2025, 6, 26, 14, 30, 0),
            datetime(2025, 6, 26, 15, 30, 0),
            datetime(2025, 6, 26, 16, 30, 0),
            datetime(2025, 6, 26, 17, 30, 0),
            datetime(2025, 6, 26, 18, 30, 0),
            datetime(2025, 6, 26, 19, 30, 0),
            datetime(2025, 6, 26, 20, 30, 0),
            datetime(2025, 6, 26, 21, 00, 0),
        ]
    )
    print(dummyObj.isFrequent)
    print(dummyObj.relevanceScore)