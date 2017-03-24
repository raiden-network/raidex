export class ZingChartModel {
    id: String;
    data: any;
    height: any;
    width: any;
    constructor(config: Object) {
    this.id = config['id'];
    this.data = config['data'];
    this.height = config['height'];
    this.width = config['width'];
  }
}
