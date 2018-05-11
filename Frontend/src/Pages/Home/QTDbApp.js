import drugs from '../../Helpers/drugs-brandnames-v4';
import { background_deltas_MF } from '../../Helpers/background_deltas_bins';
import DrugSelect from './DrugSelect';
import { Chart } from './HistogramFauxDOM';

class QTDbApp extends React.Component {
  constructor(props) {
    super(props);
    this.handleDeltaChange = this.handleDeltaChange.bind(this);
    this.handleSexChange = this.handleSexChange.bind(this);
    this.state = {drugs: [],
      deltas: [background_deltas_MF],
      deltas_overlay: [],
      males: true,
      females: true,
      histogramWidth: window.innerWidth < 625 ? (window.innerWidth-50) : 625,
      histogramHeight: 350
    };
  }

  handleDeltaChange(new_backgrounds,new_deltas,new_drugs) {
      // Update background
      var backgrounds = this.state.deltas;
      console.log("handleDeltaChange new_drugs:", new_drugs, "new_backgrounds.length:", new_backgrounds.length);


      if (new_drugs.length == 0) {
          console.log("new_drugs.length == 0");
          backgrounds = [background_deltas_MF];
      }
      else if (new_drugs.length == 1) {
          console.log("new_drugs.length == 1",new_drugs);
          backgrounds = [background_deltas_MF];
      }
      else if (new_drugs.length + 1 < backgrounds.length) { // removing drug
          console.log("new_drugs.length + 1 < backgrounds.length");

          // Remove array from backgrounds that is no longer in new_drugs
          var prev_drugs = this.state.drugs;

          var j = prev_drugs.length;
          while (j--) {
              if (new_drugs.indexOf(prev_drugs[j]) == -1) {
                  console.log("Removing background at index", j+1, prev_drugs[j]);
                  backgrounds.splice(j+1, 1);
              }
          }
      }
      else if (new_drugs.length == 2) {
          console.log("new_drugs.length == 2");
          backgrounds = [background_deltas_MF, this.state.deltas_overlay, new_backgrounds];
      }
      else if (new_drugs.length + 1 > backgrounds.length) { // adding drug
          console.log("new_drugs.length + 1 > backgrounds.length");
          backgrounds.push(new_backgrounds);
      }

      this.setState({drugs: new_drugs,
                     deltas: backgrounds,
                     deltas_overlay: new_deltas}, () => {
          console.log("deltas", this.state.deltas);
          this.refs.histogram.updateData();
      });
  }

  handleSexChange(m_bool,f_bool) {
      this.setState({males: m_bool,
                     females: f_bool}, () => {
          this.refs.histogram.updateData();
      });
  }

  // Adapted from https://www.hawatel.com/blog/handle-window-resize-in-react
  updateDimensions() {
    if(window.innerWidth >= 625) {
      this.setState({ histogramWidth: 625}, () => {
          this.refs.histogram.resize();
      });
    } else {
      this.setState({ histogramWidth: window.innerWidth-50}, () => {
          this.refs.histogram.resize();
      });
    }
  }

  componentDidMount() {
    this.updateDimensions();
    window.addEventListener("resize", this.updateDimensions.bind(this));
  }

  render() {
    return <div>
      <DrugSelect
        deltas_overlay={this.state.deltas_overlay}
        males={this.state.males}
        females={this.state.females}
        onDeltaChange={(new_backgrounds,new_deltas,new_drugs) => this.handleDeltaChange(new_backgrounds,new_deltas,new_drugs)}
        onSexChange={(m_bool,f_bool) => this.handleSexChange(m_bool,f_bool)} />
      <Chart
        ref="histogram"
        drugs={this.state.drugs}
        deltas={this.state.deltas}
        deltas_overlay={this.state.deltas_overlay}
        males={this.state.males}
        females={this.state.females}
        width={this.state.histogramWidth}
        height={this.state.histogramHeight}/>
    </div>;
  }
}

export default QTDbApp;


//******************************************
// Event listeners for saving plots and data
document.getElementById("download-plots").addEventListener("click", function() {
    var selectedDrugs = document.getElementsByName("selected-drugs")[0].value;

    if (selectedDrugs == "") {
        alert("No drugs selected");
    } else {
        print();
    }
});

document.getElementById("download-whole-db").addEventListener("click", function() {showDownloadDescription(); window.location.href = "#download";} );
document.getElementById("download-partial-db").addEventListener("click", downloadPartialData);

function downloadPartialData() {
    var selectedDrugs = document.getElementsByName("selected-drugs")[0].value;
    // console.log("selectedDrugs",selectedDrugs);

    if (selectedDrugs == "") {
        alert("No drugs selected");
    } else {
        document.getElementById('loading-csv-icon').style.display='';
        var drugNames = "";
        $.each(selectedDrugs.split(','), function(index, value){
            drugNames = drugNames.concat(drugMap[value].toLowerCase(),",");
        });
        drugNames = drugNames.slice(0,-1);
        //console.log(drugNames);
        var filename = "qtdb_"+drugNames+".csv";

        var api_call = '/api/v1/csv?drugs='+selectedDrugs;
        console.log(api_call);

        // Adapted from https://gist.github.com/grsabreu/9db117ec09162ea02075717a75ab28ee
        fetch(api_call)
            .then(function(response) {
                return (response.status == 413) ? null : response.blob();
                // 413: Payload Too Large
            })
            .then(function(blob) {
                document.getElementById('loading-csv-icon').style.display='none';
                if (blob) {
                  saveAs(blob, filename);
                  showDownloadDescription();
                  window.location.href = "#download";
                } else {
                  alert('Too many patients selected for timely CSV generation. Please download the entire database instead.');
                }
            })
            .catch(function(ex) {
                document.getElementById('loading-csv-icon').style.display='none';
                alert('Save failed');
            });
    }
}

function showDownloadDescription() {
    document.getElementById('downloadInfo').style.display='';
}