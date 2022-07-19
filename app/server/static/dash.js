function barchart(hotel){
    var trace1 = {
        x: hotel.hotel.date,
        y: hotel.hotel.tol,
        type: 'bar',
        name: 'Hotels.com',
        marker: {
          color: 'rgb(255,22,9)',
          opacity: 0.7,
        }
      };
    var trace2 = {
        x: hotel.booking.date,
        y: hotel.booking.tol,
        type: 'bar',
        name: 'Booking.com',
        marker: {
        color: 'rgb(49,130,189)',
        opacity: 0.9
        }
    };
    var trace3 = {
        x: hotel.agoda.date,
        y: hotel.agoda.tol,
        type: 'bar',
        name: 'Agoda.com',
        marker: {
        color: 'rgb(100,204,204)',
        opacity: 1
        }
    };
    var trace4 = {
        x: hotel.hotel.date,
        y: hotel.tol,
        type: 'bar',
        name: 'Total',
        marker: {
        color: 'rgb(25,25,122)',
        opacity: 0.7
        }
    };

    var data = [trace1, trace2, trace3, trace4];
    var layout = {
        title: {
            text:'<b>Hotel Crawler Number</b>',
            font: {
                family: 'Arial, serif',
                size: 24
              }, xref: 'paper',
        },
        legend: {
            font: {
                family: 'Arial, serif',
                size: 10,
            }
        },
        margin: {autoexpand:true, b: 100},
        xaxis: {
            linecolor: 'grey',
            linewidth: 2,
            tickangle: -35,
            type: "category",
            title: {
                text: 'Date',
                font: {
                    family: 'Arial, serif',
                    size: 15,
                }
            },barmode: 'group'
        },
        yaxis: {
            linecolor: 'grey',
            linewidth: 2,
            title: {
                text: 'Number of Hotels Data (count)',
                font: {
                        family: 'Arial, serif',
                    size: 15,
                }
            }
        }
    };
    Plotly.newPlot('barchart', data, layout);
}

function pipe1_time(data){
    var trace1 = {
      x: data.date,
      y: data.spend,
      type: 'scatter'
    };

    var data = [trace1];
    var layout = {
        title: {
            text:'<b>Hotel Crawler Runtime</b>',
            font: {
                family: 'Arial, serif',
                size: 24
              }, xref: 'paper',
        },
        legend: {
            font: {
                family: 'Arial, serif',
                size: 10,
            }
        },
        margin: {autoexpand:true, b: 100},
        xaxis: {
            linecolor: 'grey',
            linewidth: 2,
            tickangle: -35,
            type: "category",
            title: {
                text: 'Date',
                font: {
                    family: 'Arial, serif',
                    size: 15,
                }
            },barmode: 'group'
        },
        yaxis: {
            linecolor: 'grey',
            linewidth: 2,
            title: {
                text: 'Time (hr)',
                font: {
                        family: 'Arial, serif',
                    size: 15,
                }
            }
        }
    };
    Plotly.newPlot('pipe1_time', data, layout);
}

function pipe1_accu(data){
    var trace1 = {
        x: data.hotel.date,
        y: data.hotel.accu,
        type: 'bar',
        name: 'Hotels.com',
        marker: {
          color: 'rgb(255,22,9)',
          opacity: 0.7,
        }
      };
    var trace2 = {
        x: data.booking.date,
        y: data.booking.accu,
        type: 'bar',
        name: 'Booking.com',
        marker: {
        color: 'rgb(49,130,189)',
        opacity: 0.9
        }
    };
    var trace3 = {
        x: data.agoda.date,
        y: data.agoda.accu,
        type: 'bar',
        name: 'Agoda.com',
        marker: {
        color: 'rgb(100,204,204)',
        opacity: 1
        }
    };
    var trace4 = {
        x: data.hotel.date,
        y: data.total.accu,
        type: 'bar',
        name: 'Total',
        marker: {
        color: 'rgb(25,25,122)',
        opacity: 0.7
        }
    };

    var data = [trace1, trace2, trace3, trace4];
    var layout = {
        title: {
            text:'<b>Hotel Pipeline Accuracy</b>',
            font: {
                family: 'Arial, serif',
                size: 24
              }, xref: 'paper',
        },
        legend: {
            font: {
                family: 'Arial, serif',
                size: 10,
            }
        },
        margin: {autoexpand:true, b: 100},
        xaxis: {
            linecolor: 'grey',
            linewidth: 2,
            type: "category",
            title: {
                text: 'Date',
                font: {
                    family: 'Arial, serif',
                    size: 15,
                }
            },barmode: 'group'
        },
        yaxis: {
            linecolor: 'grey',
            linewidth: 2,
            title: {
                text: 'Accuracy (%)',
                font: {
                        family: 'Arial, serif',
                    size: 15,
                }
            }
        }
    };
    Plotly.newPlot('pipe1_accu', data, layout);
}

function pipe2_price(data){
    var trace1 = {
        x: data.hotel.date,
        y: data.hotel.price,
        type: 'bar',
        name: 'Hotels.com',
        marker: {
          color: 'rgb(255,22,9)',
          opacity: 0.7,
        }
      };
    var trace2 = {
        x: data.booking.date,
        y: data.booking.price,
        type: 'bar',
        name: 'Booking.com',
        marker: {
        color: 'rgb(49,130,189)',
        opacity: 0.9
        }
    };
    var trace3 = {
        x: data.agoda.date,
        y: data.agoda.price,
        type: 'bar',
        name: 'Agoda.com',
        marker: {
        color: 'rgb(100,204,204)',
        opacity: 1
        }
    };

    var data = [trace1, trace2, trace3];
    var layout = {
        title: {
            text:'<b>Price Crawler Number</b>',
            font: {
                family: 'Arial, serif',
                size: 24
              }, xref: 'paper',
        },
        legend: {
            font: {
                family: 'Arial, serif',
                size: 10,
            }
        },
        margin: {autoexpand:true, b: 100},
        xaxis: {
            linecolor: 'grey',
            linewidth: 2,
            type: "category",
            title: {
                text: 'Date',
                font: {
                    family: 'Arial, serif',
                    size: 15,
                }
            },barmode: 'group'
        },
        yaxis: {
            linecolor: 'grey',
            linewidth: 2,
            title: {
                text: 'Number of Price Data (count)',
                font: {
                        family: 'Arial, serif',
                    size: 15,
                }
            }
        }
    };
    Plotly.newPlot('pipe2_price', data, layout);
}

function pipe2_time(data){
    var trace1 = {
      x: data.hotel.date,
      y: data.hotel.spend,
      type: 'scatter',
      name: 'Hotels.com',
      marker: {
        color: 'rgb(255,22,9)',
        opacity: 0.7,
      }
    };
    var trace2 = {
      x: data.booking.date,
      y: data.booking.spend,
      type: 'scatter',
      name: 'Booking.com',
      marker: {
      color: 'rgb(49,130,189)',
      opacity: 0.9
      }
    };
    var trace3 = {
      x: data.agoda.date,
      y: data.agoda.spend,
      type: 'scatter',
      name: 'Agoda.com',
      marker: {
      color: 'rgb(100,204,204)',
      opacity: 1
      }
    };

    var data = [trace1, trace2, trace3];
    var layout = {
        title: {
            text:'<b>Price Crawler Runtime</b>',
            font: {
                family: 'Arial, serif',
                size: 24
              }, xref: 'paper',
        },
        legend: {
            font: {
                family: 'Arial, serif',
                size: 10,
            }
        },
        margin: {autoexpand:true, b: 100},
        xaxis: {
            linecolor: 'grey',
            linewidth: 2,
            type: "category",
            title: {
                text: 'Date',
                font: {
                    family: 'Arial, serif',
                    size: 15,
                }
            },barmode: 'group'
        },
        yaxis: {
            linecolor: 'grey',
            linewidth: 2,
            title: {
                text: 'Time (hr)',
                font: {
                        family: 'Arial, serif',
                    size: 15,
                }
            }
        }
    };
    Plotly.newPlot('pipe2_time', data, layout);
}

fetch('/admin/fetch_data')
  .then(function(res) {
    return res.json();
  })
  .then(function(myjson) {
    let hotel = myjson.hotel_pack;
    let price = myjson.price_pack;
    let time = myjson.time_pack;
    let accu = myjson.accu_pack;
    let text = myjson.text_pack;
    barchart(hotel)
    pipe1_time(time.pipe1)
    pipe1_accu(accu)
    pipe2_price(price)
    pipe2_time(time.pipe2)
    var h = document.querySelector('#hotel')
    h.innerHTML = text.hotel
    var p = document.querySelector('#price')
    p.innerHTML = text.price
  });



