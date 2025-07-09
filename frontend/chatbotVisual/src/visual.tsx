"use strict";

import * as React from "react";
import * as ReactDOMClient from "react-dom/client";   // ⬅️ import client API
import powerbi from "powerbi-visuals-api";
import { FormattingSettingsService } from "powerbi-visuals-utils-formattingmodel";
import "./style/visual.less";

import VisualConstructorOptions = powerbi.extensibility.visual.VisualConstructorOptions;
import VisualUpdateOptions = powerbi.extensibility.visual.VisualUpdateOptions;
import IVisual = powerbi.extensibility.visual.IVisual;

import { VisualFormattingSettingsModel } from "./settings";
import  ChatApp  from "./ChatApp/ChatApp";

export class Visual implements IVisual {
    private formattingSettingsService = new FormattingSettingsService();
    private formattingSettings: VisualFormattingSettingsModel = new VisualFormattingSettingsModel();
    private root: ReactDOMClient.Root;   // giữ tham chiếu để unmounts

    constructor(options: VisualConstructorOptions) {
        // ⬇️ Tạo React Root & render
        this.root = ReactDOMClient.createRoot(options.element);
        this.root.render(<ChatApp />);
    }

    public update(options: VisualUpdateOptions) {
        if (options.dataViews?.length) {
            this.formattingSettings = this.formattingSettingsService
                .populateFormattingSettingsModel(VisualFormattingSettingsModel, options.dataViews[0]);
        }
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel {
        // luôn truyền object hợp lệ (đã khởi tạo mặc định ở trên)
        return this.formattingSettingsService.buildFormattingModel(this.formattingSettings);
    }

    public destroy() {
        // ⬇️ API mới của React 18
        this.root.unmount();
    }
}
