from cmfg.model import SMfgModel, LAST_STEP

model = SMfgModel()

for _ in range(LAST_STEP):
    model.step()