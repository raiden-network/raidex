export class ZingChartModel {
    public id: string;
    public data: any;
    public height: any;
    public width: any;

    constructor(config: Object) {
        this.id = config['id'];
        this.data = config['data'];
        this.height = config['height'];
        this.width = config['width'];
    }
}
