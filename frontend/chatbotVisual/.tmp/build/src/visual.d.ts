import powerbi from "powerbi-visuals-api";
import "./style/visual.less";
import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import IVisual = powerbi.extensibility.visual.IVisual;
export declare class Visual implements IVisual {
    private formattingSettingsService;
    private formattingSettings;
    private root;
    constructor(options: VisualConstructorOptions);
    update(options: VisualUpdateOptions): void;
    getFormattingModel(): powerbi.visuals.FormattingModel;
    destroy(): void;
}
