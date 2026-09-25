"""Risk assessments require a separately validated rule engine and measured inputs."""


class RiskEvaluator:
    def __init__(self, rule_file_path=None):
        self.rule_file_path = rule_file_path

    def evaluate(self, feature: dict, context: dict = None) -> dict:
        return {
            "risk_level": "UNKNOWN",
            "evaluation_status": "NOT_EVALUATED",
            "reason": "검증된 위험도 규칙과 동일 시공간의 선박·수심·항로 근거가 연결되지 않았습니다.",
        }

    async def aevaluate(self, feature: dict, context: dict = None) -> dict:
        return self.evaluate(feature, context)


risk_evaluator = RiskEvaluator()
