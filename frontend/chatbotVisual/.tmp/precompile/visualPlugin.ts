import { Visual } from "../../src/visual";
import powerbiVisualsApi from "powerbi-visuals-api";
import IVisualPlugin = powerbiVisualsApi.visuals.plugins.IVisualPlugin;
import VisualConstructorOptions = powerbiVisualsApi.extensibility.visual.VisualConstructorOptions;
import DialogConstructorOptions = powerbiVisualsApi.extensibility.visual.DialogConstructorOptions;
var powerbiKey: any = "powerbi";
var powerbi: any = window[powerbiKey];
var chatbotVisual6F62CEA04C6E48689C09B7E1A9751D1F: IVisualPlugin = {
    name: 'chatbotVisual6F62CEA04C6E48689C09B7E1A9751D1F',
    displayName: 'Chatbot Visual',
    class: 'Visual',
    apiVersion: '5.7.0',
    create: (options?: VisualConstructorOptions) => {
        if (Visual) {
            return new Visual(options);
        }
        throw 'Visual instance not found';
    },
    createModalDialog: (dialogId: string, options: DialogConstructorOptions, initialState: object) => {
        const dialogRegistry = (<any>globalThis).dialogRegistry;
        if (dialogId in dialogRegistry) {
            new dialogRegistry[dialogId](options, initialState);
        }
    },
    custom: true
};
if (typeof powerbi !== "undefined") {
    powerbi.visuals = powerbi.visuals || {};
    powerbi.visuals.plugins = powerbi.visuals.plugins || {};
    powerbi.visuals.plugins["chatbotVisual6F62CEA04C6E48689C09B7E1A9751D1F"] = chatbotVisual6F62CEA04C6E48689C09B7E1A9751D1F;
}
export default chatbotVisual6F62CEA04C6E48689C09B7E1A9751D1F;