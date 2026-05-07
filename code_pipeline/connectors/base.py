from abc import ABC, abstractmethod

class HostConnector(ABC):
    """
    모든 코드 생성 엔진에 공통으로 요구되는 인터페이스 정의.
    """

    @abstractmethod
    def cultivate(self, prompt: str) -> str:
        """프롬프트를 입력받아 코드 문자열을 생성합니다."""
        pass

    @property
    @abstractmethod
    def connector_name(self) -> str:
        """커넥터 식별자 문자열."""
        pass