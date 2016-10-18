import { RexmigrationPage } from './app.po';

describe('rexmigration App', function() {
  let page: RexmigrationPage;

  beforeEach(() => {
    page = new RexmigrationPage();
  });

  it('should display message saying app works', () => {
    page.navigateTo();
    expect(page.getParagraphText()).toEqual('app works!');
  });
});
